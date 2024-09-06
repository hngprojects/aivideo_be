import asyncio
import csv
from datetime import datetime, timedelta, timezone
from io import StringIO
import json
from time import sleep
from typing import Optional
from fastapi import HTTPException
from fastapi import status as HTTPStatus
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from celery.result import AsyncResult

from api.core.dependencies.celery.celery_app import worker
from api.v1.models.job import Job
from api.v1.models.project import Project
from api.v1.models.user import User
from api.v1.schemas.project import CreateProject
from api.v1.services.project import project_service
from sqlalchemy.orm import joinedload
from sqlalchemy import or_, desc


class JobService:
    """This is for job db operations"""

    def get_job_status(self, db: Session, job_id: str):
        """Returns the status of a partiular job"""

        task_result = AsyncResult(job_id, app=worker)
        return task_result.state

    def create_project_with_job(
        self,
        db: Session,
        job,
        project_title: str,
        project_type: str,
        user_id: Optional[str] = None,
        description: Optional[str] = None,
    ):
        """FUnction to create a project alongside a task or job"""

        # Create project based on task run
        project_schema = CreateProject(
            title=project_title,
            project_type=project_type,
            user_id=user_id,
            description=description,
        )
        project = project_service.create(db=db, schema=project_schema)

        # Create celery task
        self.create_job(db=db,job_id=job.id, project_id=project.id, user_id=user_id)

        return project

    def create_job(
        self,
        db: Session,
        job_id: str,
        project_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ):
        """Creates a new celery job"""

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

    def fetch_all_jobs(self, db: Session):
        """Fetches all celery jobs from the database"""

        jobs = db.query(Job).all()
        return jobs

    def fetch_by_job_id(self, db: Session, job_id: str):
        """Fetches the job details from the database"""

        job = db.query(Job).filter(Job.job_id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Celery job not found")
        return job

    def update_job(
        self, 
        db: Session,
        job_id: str, 
        status: str, 
        result: Optional[str] = None, 
        user_id: Optional[str] = None
    ):
        """Updates the job details with option to link to a user"""

        try:
            job = self.fetch_by_job_id(db=db, job_id=job_id)
            job.status = status
            job.result = result if result is not None else None
            job.user_id = user_id if user_id is not None else None
            db.commit()
            db.refresh(job)
            return job
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=400, detail=f"{type(e).__name__} occurred. {repr(e)}"
            )

    def get_project_from_job(self, db: Session, job_id: str):
        """Returns the project from the job details"""

        job = self.fetch_by_job_id(db=db, job_id=job_id)
        project = db.query(Project).filter(Project.id == job.project_id).first()

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        return project

    def update_job_result(self, db: Session, job_id: str):
        """Fetches the result from celery and updates the job"""
        task_result = AsyncResult(job_id, app=worker)

        if task_result.state == "SUCCESS":
            result = task_result.get()
            self.update_job(db=db, job_id=job_id, status=task_result.state, result=result)
        elif task_result.state in ["FAILURE", "REVOKED"]:
            self.update_job(db=db, job_id=job_id, status=task_result.state)

    def fetch_job_activity(
        self,
        db: Session,
        page: int = 1,
        per_page: int = 10,
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

        # search by job_id, User first name and last name

        if search:
            search_filters = [
                Job.job_id.icontains(f"%{search}%"),
                Job.user.has(
                    or_(
                        User.first_name.icontains(f"%{search}%"),
                        User.last_name.icontains(f"%{search}%"),
                        User.email.icontains(f"%{search}%"),
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
        total: int = query.count()

        jobs = (
            query.order_by(desc(Job.created_at))
            .limit(per_page)
            .offset((page - 1) * per_page)
            .all()
        )


        jobs = jsonable_encoder(jobs)

        total_pages = int(total / per_page) + (total % per_page > 0)

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
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages,
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
        one_hour_ago = datetime.now(timezone(timedelta(hours=1))) - timedelta(hours=1)

        query = db.query(Job)

        total_tasks = query.count()
        active_users = db.query(User).filter(User.is_active == True)
        failed_tasks = query.filter(Job.status.icontains("FAILED"))
        in_progress_tasks = query.filter(
            or_(Job.status.icontains("STARTED"), Job.status.icontains("RUNNING"))
        )
        pending_tasks = query.filter(Job.status.icontains("PENDING"))
        completed_tasks = query.filter(Job.status.icontains("SUCCESS"))

        created_in_last_hour = query.filter(Job.created_at >= one_hour_ago).count()

        active_in_last_hour = in_progress_tasks.filter(
            Job.created_at >= one_hour_ago
        ).count()

        pending_in_last_hour = pending_tasks.filter(
            Job.created_at >= one_hour_ago
        ).count()

        completed_in_last_hour = completed_tasks.filter(
            Job.created_at >= one_hour_ago
        ).count()

        stats = {
            "total_tasks": total_tasks,
            "active_users": active_users.count(),
            "failed_tasks": failed_tasks.count(),
            "in_progress_tasks": in_progress_tasks.count(),
            "pending_tasks": pending_tasks.count(),
            "completed_tasks": completed_tasks.count(),
            "created_in_last_hour": created_in_last_hour,
            "active_in_last_hour": active_in_last_hour,
            "pending_in_last_hour": pending_in_last_hour,
            "completed_in_last_hour": completed_in_last_hour,
        }

        return stats

    async def stream_job_statistics(self, db: Session):
        """SSE handler to stream job statistics"""

        initial: str = ""

        while True:
            stats = self.get_job_statistics(db=db)

            data = json.dumps(stats)

            if data != initial:
                yield f"data: {data}\n\n"
                initial = data

            await asyncio.sleep(1)

    async def stream_job_activity(self, db: Session):
        """SSE handler to stream job activities"""

        initial: str = ""

        try:
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

                for job in list(jobs):
                    if job.get("user"):
                        user_data = job.get("user")

                        for key, _ in list(user_data.items()):
                            if key == "password":
                                del user_data[key]
                                break

                data = json.dumps(jobs)

                if data != initial:
                    yield f"data: {data}\n\n"
                    initial = data

                await asyncio.sleep(1)
                
        except Exception as e:
            pass

    def fetch_recent_job_activity(self, db: Session):
        query = db.query(Project, Job).outerjoin(Job, Project.id == Job.project_id)
        query_result = query.order_by(desc(Job.created_at)).limit(10).all()
        all_tasks = [
            {
                "id": project.id,
                "created_at": project.created_at,
                "status": job.status,
                "tool_used": project.project_type,
            }
            for project, job in query_result
        ]

        return all_tasks


job_service = JobService()
