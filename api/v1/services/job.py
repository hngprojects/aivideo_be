import csv
from io import StringIO
from typing import Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session
from celery.result import AsyncResult

from api.core.dependencies.celery.celery_app import worker
from api.db.database import get_db
from api.utils.pagination import paginated_response
from api.v1.models.job import Job
from api.v1.models.project import Project
from api.v1.schemas.project import CreateProject
from api.v1.services.project import project_service


db = next(get_db())


class JobService:
    """This is for job db operations"""

    def get_job_status(self, job_id: str):
        """Returns the status of a partiular job"""

        task_result = AsyncResult(job_id, app=worker)
        return task_result.state

    def create_project_with_job(self, job, project_title: str, project_type: str):
        """FUnction to create a project alongside a task or job"""

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

    def create_job(self, job_id: str, project_id: str, user_id: Optional[str] = None):
        """Creates a new celery job"""

        job = Job(
            job_id=job_id, project_id=project_id, user_id=user_id, status="RUNNING"
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        return job

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

        job = self.fetch_by_job_id(job_id=job_id)

        job.status = status
        job.result = result if result is not None else None
        db.commit()
        db.refresh(job)
        return job

    def get_project_from_job(self, job_id: str):
        """Returns the project from the job details"""

        job = self.fetch_by_job_id(job_id=job_id)
        project = db.query(Project).filter(
            Project.id == job.project_id).first()

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
    def fetch_job_activity(self, db: Session, skip: int, limit: int, filters: dict):
        return paginated_response(
            db=db,
            model=Job,
            skip=skip,
            limit=limit,
            filters=filters,
            related_models=[Job.user, Job.project],
            related_model_excludes={
                "user": [
                    "password",
                    "is_superadmin",
                    "is_deleted",
                    "created_at",
                    "update_at",
                    "avatar_url",
                    "is_active",
                    "email",
                    "created_at",
                    "updated_at",
                ],
                "project": [
                    "title",
                    "description",
                    "file_url",
                    "archived",
                    "result",
                    "is_deleted",
                ],
            },
        )

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
                    datum.user.first_name,
                    datum.user.last_name,
                    datum.user.email,
                    datum.job_id,
                    datum.project.project_type,
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
        stats["failed_tasks"] = query.filter(getattr(Job, "status").ilike(f"%failed%")).count()
        stats["in_progress_tasks"] = query.filter(getattr(Job, "status").ilike(f"%inprogress%")).count()
        stats["pending_tasks"] = query.filter(getattr(Job, "status").ilike(f"%pending%")).count()
        stats["completed_tasks"] = query.filter(getattr(Job, "status").ilike(f"%completed%")).count()

        return stats


job_service = JobService()
