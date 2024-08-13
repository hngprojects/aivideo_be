from typing import Optional
from fastapi import HTTPException

from api.db.database import get_db
from api.v1.models.job import Job
from api.v1.models.project import Project
from api.v1.schemas.project import CreateProject
from api.v1.services.project import project_service


db = next(get_db())

class JobService:
    '''This is for job db operations'''

    def create_project_with_job(self, job, project_title: str, project_type: str):
        '''FUnction to create a project alongside a task or job'''

        # Create project based on task run
        project_schema = CreateProject(
            title=project_title,
            project_type=project_type,
        )
        project = project_service.create(db=db, schema=project_schema)

        # Create celery task
        self.create_job(job_id=job.id, project_id=project.id)

        return project


    def create_job(self, job_id: str, project_id: str):
        '''Creates a new celery job'''

        job = Job(
            job_id=job_id, 
            project_id=project_id, 
            status='RUNNING'
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        return job
    

    def fetch_all_jobs(self):
        '''Fetches all celery jobs from the database'''

        jobs = db.query(Job).all()
        return jobs

    
    def fetch_by_job_id(self, job_id: str):
        '''Fetches the job details from the database'''

        job = db.query(Job).filter(Job.job_id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail='Celery job not found')
        return job


    def update_job(self, job_id: str, status: str, result: Optional[str] = None):
        '''Updates the job details'''

        job = self.fetch_by_job_id(job_id=job_id)

        job.status = status
        job.result = result if result is not None else None
        db.commit()
        return job
    
    def get_project_from_job(self, job_id: str):
        '''Returns the project from the job details'''

        job = self.fetch_by_job_id(job_id=job_id)
        project = db.query(Project).filter(Project.id == job.project_id).first()

        if not project:
            raise HTTPException(status_code=404, detail='Project not found')
        return project
    



job_service = JobService()
