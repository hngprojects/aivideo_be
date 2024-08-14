from fastapi import APIRouter, Depends, status, BackgroundTasks
from typing import List
from api.v1.schemas.job import JobResponse
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from api.db.database import get_db
from api.utils.pagination import paginated_response
from api.v1.models.job import Job
from api.v1.models.user import User
from api.v1.services.user import user_service
from api.v1.services.job import job_service

job = APIRouter(prefix="/jobs", tags=["Jobs"])

# Get all jobs
@job.get("/", response_model=List[JobResponse], status_code=status.HTTP_200_OK)
async def get_all_jobs():
    """Fetch all jobs from the database."""
    jobs = job_service.fetch_all_jobs()
    return jobs

# Get a job by its ID
@job.get("/{job_id}/update_result", response_model=JobResponse)
async def update_job_result(job_id: str, background_tasks: BackgroundTasks):
    '''Endpoint to update the job result after the task is completed'''
    
    def update_result_task(job_id: str):
        job_service.update_job_result(job_id)

    background_tasks.add_task(update_result_task, job_id)
    return job_service.fetch_by_job_id(job_id)



@job.get("/activity")
async def get_managed_jobs(
    current_admin: User = Depends(user_service.get_current_super_admin),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 30,
    filters: dict = {},
):
    return job_service.fetch_job_activity(
        db=db, skip=skip, limit=limit, filters=filters
    )


@job.get("/export")
async def export_jobs_as_csv(
    db: Session = Depends(get_db),
    current_admin: User = Depends(user_service.get_current_super_admin),
):
    csv_file = job_service.export_jobs_as_csv(db)

    response = StreamingResponse(csv_file, media_type="text/csv")
    response.headers["Content-Disposition"] = f"attachment; filename=job-data.csv"
    response.status_code = 200

    return response
