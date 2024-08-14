from fastapi import APIRouter, Depends, status, BackgroundTasks
from typing import List
from api.v1.schemas.job import JobResponse
from api.v1.services.job import job_service

job_router = APIRouter(prefix="/jobs", tags=["Jobs"])

# Get all jobs
@job_router.get("/", response_model=List[JobResponse], status_code=status.HTTP_200_OK)
async def get_all_jobs():
    """Fetch all jobs from the database."""
    jobs = job_service.fetch_all_jobs()
    return jobs

# Get a job by its ID
@job_router.get("/{job_id}/update_result", response_model=JobResponse)
async def update_job_result(job_id: str, background_tasks: BackgroundTasks):
    '''Endpoint to update the job result after the task is completed'''
    
    def update_result_task(job_id: str):
        job_service.update_job_result(job_id)

    background_tasks.add_task(update_result_task, job_id)
    return job_service.fetch_by_job_id(job_id)

