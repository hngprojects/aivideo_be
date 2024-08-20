import asyncio
import csv
from io import StringIO
import json
from time import sleep
from typing import Optional
from fastapi import HTTPException
from fastapi import status as HTTPStatus
from fastapi.encoders import jsonable_encoder
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from celery.result import AsyncResult

from api.core.dependencies.celery.celery_app import worker
from api.db.database import get_db
from api.v1.models.job import Job
from api.v1.models.project import Project
from api.v1.models.user import User
from api.v1.schemas.project import CreateProject
from api.v1.services.project import project_service
from sqlalchemy.orm import joinedload
from sqlalchemy import or_, desc


db = next(get_db())


class JobService:
    """This is for job db operations"""

    def get_job_status(self, job_id: str):
        """Returns the status of a partiular job"""

        task_result = AsyncResult(job_id, app=worker)
        return task_result.state

    def create_project_with_job(
        self, job, project_title: str, project_type: str, user_id: Optional[str] = None
    ):
        """FUnction to create a project alongside a task or job"""

        # Create project based on task run
        project_schema = CreateProject(title=project_title, project_type=project_type)
        project = project_service.create(db=db, schema=project_schema)

        # Create celery task
        self.create_job(job_id=job.id, project_id=project.id, user_id=user_id)

        return project

    def create_job(
        self,
        job_id: str,
        project_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ):
        """Creates a new celery job"""

        job = Job(
            job_id=job_id, project_id=project_id, user_id=user_id, status="RUNNING"
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        return job
        try:
            job = Job(
                job_id=job_id, 
                project_id=project_id, 
                user_id=user_id, 
                status="Pending"
            )
            db.add(job)
            db.commit()
            db.refresh(job)
            return job
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Error {e}")

    def fetch_all_jobs(self):
        """Fetches all celery jobs from the database"""

        jobs = db.query(Job).all()
        return jobs

    def fetch_by_job_id(self, job_id: str):
        """Fetches the job details from the database"""

        job = db.query(Job).filter(Job.job_id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Celery job not found")
        return job

    def update_job(self, job_id: str, status: str, result: Optional[str] = None):
        """Updates the job details"""

        try:
            job = self.fetch_by_job_id(job_id=job_id)
            job.status = status
            job.result = result if result is not None else None
            db.commit()
            db.refresh(job)
            return job
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=400, detail=f"{type(e).__name__} occurred. {repr(e)}"
            )

    def get_project_from_job(self, job_id: str):
        """Returns the project from the job details"""

        job = self.fetch_by_job_id(job_id=job_id)
        project = db.query(Project).filter(Project.id == job.project_id).first()

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        return project

    def update_job_result(self, job_id: str):
        """Fetches the result from celery and updates the job"""
        task_result = AsyncResult(job_id, app=worker)

        if task_result.state == "SUCCESS":
            result = task_result.get()
            self.update_job(job_id=job_id, status=task_result.state, result=result)
        elif task_result.state in ["FAILURE", "REVOKED"]:
            self.update_job(job_id=job_id, status=task_result.state)

    def fetch_job_activity(
        self,
        db: Session,
        skip: int,
        limit: int,
        search: str = "",
        status: Optional[list[str]] = None,
        project_type: Optional[list[str]] = None,
    ):
        """
        Retrieve a list of jobs with related project and user data, filtered by various criteria and paginated.

        Args:
            :param db (Session): The SQLAlchemy database session used for querying the database.
            :param skip (int): The number of records to skip (used for pagination).
            :param limit (int): The maximum number of records to return (used for pagination).
            :param search (str, optional): A string used to search for jobs based on job ID, user's first name, or user's last name. Defaults to an empty string.
            :param status (Optional[List[str]], optional): A list of job statuses to filter the results. Jobs will be included if their status matches any item in this list. Defaults to None, which means no status filter is applied.
            :param project_type (Optional[List[str]], optional): A list of project types to filter the results. Jobs will be included if their associated project's type matches any item in this list. Defaults to None, which means no project type filter is applied.

        Returns:
            dict: A dictionary containing the paginated list of jobs and related data, along with pagination metadata.
                - status_code (int): The HTTP status code for the operation (always 200 for successful fetch).
                - message (str): A message indicating the success of the operation.
                - data (dict): A dictionary containing the returned data.

        Raises:
            None: This function does not raise any exceptions directly but may propagate exceptions from the database query or data processing if errors occur.
        """

        query = db.query(Job).options(
            joinedload(Job.project),
            joinedload(Job.user),
        )

        total: int = query.count()

        # search by job_id, User first name and last name

        if search:
            search_filters = [
                Job.job_id.icontains(f"%{search}%"),
                Job.user.has(
                    or_(
                        User.first_name.icontains(f"%{search}%"),
                        User.last_name.icontains(f"%{search}%"),
                    )
                ),
            ]

            query = query.filter(or_(*search_filters))

        # Status filter

        if status and any(status):
            status_conditions = [Job.status.ilike(f"%{s}%") for s in status if s]
            query = query.filter(or_(*status_conditions))

        # Project-Type filter

        if project_type and any(project_type):
            project_type_conditions = [
                Job.project.has(Project.project_type.ilike(f"%{pt}%"))
                for pt in project_type
                if pt
            ]
            query = query.filter(or_(*project_type_conditions))

        # paginate response

        jobs = query.order_by(desc(Job.created_at)).offset(skip).limit(limit).all()

        jobs = jsonable_encoder(jobs)

        # Remove the password field from user data

        for job in jobs:
            if job.get("user"):
                user_data = job.get("user")
                if "password" in user_data:
                    del user_data["password"]

        # dashboard statistics

        stats = self.get_job_statistics(db)

        return {
            "status_code": HTTPStatus.HTTP_200_OK,
            "message": "Successfully fetched jobs",
            "data": {
                "skip": skip,
                "limit": limit,
                "jobs": jobs,
                "stats": stats,
            },
        }

    def export_jobs_as_csv(self, db: Session):
        # get videos

        data = db.query(Job).all()

        csv_file = StringIO()
        csv_writer = csv.writer(csv_file)

        csv_writer.writerow(
            [
                "ID",
                "Firstname",
                "Lastname",
                "Email",
                "Task ID",
                "Project Type",
                "Date Created",
                "Status",
            ]
        )

        for datum in data:
            csv_writer.writerow(
                [
                    datum.id,
                    datum.user.first_name if datum.user else None,
                    datum.user.last_name if datum.user else None,
                    datum.user.email if datum.user else None,
                    datum.job_id,
                    datum.project.project_type if datum.project else None,
                    datum.created_at,
                    datum.status,
                ]
            )

        csv_file.seek(0)

        return csv_file

    def get_job_statistics(self, db: Session):
        stats = {}
        query = db.query(Job)

        stats["total_tasks"] = query.count()
        stats["failed_tasks"] = query.filter(Job.status.icontains("FAILED")).count()
        stats["in_progress_tasks"] = query.filter(
            or_(Job.status.icontains("STARTED"), Job.status.icontains("RUNNING"))
        ).count()
        stats["pending_tasks"] = query.filter(Job.status.icontains("PENDING")).count()
        stats["completed_tasks"] = query.filter(Job.status.icontains("SUCCESS")).count()

        return stats

    async def stream_job_activity(self, db: Session):
        """SSE handler to stream job activities"""

        initial: str = ""

        while True:
            query = (
                db.query(Job)
                .options(
                    joinedload(Job.project),
                    joinedload(Job.user),
                )
                .order_by(Job.created_at.desc())
                .all()
            )

            jobs = jsonable_encoder(query)

            # Remove the password field from user data

            for job in jobs:
                if job.get("user"):
                    user_data = job.get("user")
                    if "password" in user_data:
                        del user_data["password"]

            data = json.dumps(jobs)

            if data != initial:
                yield f"data: {data}\n\n"
                initial = data

            await asyncio.sleep(1)


job_service = JobService()
