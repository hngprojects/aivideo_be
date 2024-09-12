from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.concurrency import run_in_threadpool
from fastapi.encoders import jsonable_encoder
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from api.core.dependencies.job_runner.app.async_runner import job_handling
from api.db.database import get_db
from api.utils.success_response import success_response
from api.v1.models.job import JobStatus
from api.v1.models.user import User
from api.v1.services.user import user_service
from api.v1.services.job import tifi_job_service
from api.core.dependencies.job_runner.app.services import regular_service, yield_service


job_running_router = APIRouter(prefix="/api/v1/jobs", tags=["Jobs"])


# Get all jobs
@job_running_router.get("", response_model=success_response, status_code=status.HTTP_200_OK)
async def get_all_jobs(db: Session = Depends(get_db)):
    """Fetch all jobs from the database."""

    jobs = tifi_job_service.fetch_all(db=db)

    return success_response(
        status_code=200,
        message='Jobs fetched successfully',
        data=jsonable_encoder(jobs)
    )


@job_running_router.get("/available", response_model=success_response, status_code=status.HTTP_200_OK)
async def get_all_available_jobs(db: Session = Depends(get_db)):
    """Fetch all jobs from the database."""

    jobs = tifi_job_service.fetch_all_available(db=db)

    return success_response(
        status_code=200,
        message='Jobs fetched successfully',
        data=jsonable_encoder(jobs)
    )


@job_running_router.get("/process-jobs-synchronous", status_code=status.HTTP_200_OK)
async def process_jobs_synchronous(db: Session = Depends(get_db)):
    """This endpoint processes all pending jobs synchronously"""

    return StreamingResponse(
        yield_service.run_pending_jobs(), 
        media_type="text/event-stream"
    )


@job_running_router.get("/retrieve-and-mark-as-processing", status_code=status.HTTP_200_OK)
async def retrieve_and_mark_as_processing(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """This endpoint processes all pending jobs asynchronously"""

    # job_handling.process_all_jobs()  # This will handle both parallel and serial jobs

    # Add the job processing task to run in the background
    background_tasks.add_task(run_in_threadpool, job_handling.process_all_jobs)

    return success_response(
        status_code=200,
        message='Pending jobs executing in the background'
    )


# @job_running_router.get("/process-jobs-async", response_model=success_response, status_code=status.HTTP_200_OK)
# async def process_jobs_asynchronous(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
#     """This endpoint processes all pending jobs asynchronously"""

#     # background_tasks.add_task(run_pending_jobs)
#     # run_pending_jobs_in_celery.delay()

#     jobs = tifi_job_service.fetch_all_pending(db=db)
#     for job in jobs:
#         run_job_in_celery.delay(job_id=job.id)

#     #     def event_generator():
#     #         for log in run_job_in_celery.delay(job_id=job.id):
#     #             yield log  # Yielding each log in real-time
    
#     # return StreamingResponse(event_generator(), media_type="text/plain")

#     return success_response(
#         status_code=200,
#         message='Pending jobs executing in the background',
#     )


@job_running_router.get("/{job_id}", response_model=success_response, status_code=status.HTTP_200_OK)
async def get_single_job(job_id: str, db: Session = Depends(get_db)):
    """Fetch a single job from the database."""

    job = tifi_job_service.fetch(db=db, job_id=job_id)

    return success_response(
        status_code=200,
        message='Job fetched successfully',
        data=jsonable_encoder(job)
    )


@job_running_router.get("/{job_id}/process", response_model=success_response, status_code=status.HTTP_200_OK)
async def process_and_execute_job(background_tasks: BackgroundTasks, job_id: str, db: Session = Depends(get_db)):
    """Processes and executes a single job from the database as long as it is pending or failed.
    This is done in the background.
    """

    job = tifi_job_service.fetch(db=db, job_id=job_id)

    if job.is_expired():
        raise HTTPException(status_code=400, detail="Job has expired")
    
    # Check if job state is valid
    if job.status not in [JobStatus.pending, JobStatus.failed]:
        raise HTTPException(status_code=400, detail="Job is not in pending or failed state")

    # background_tasks.add_task(process_job,job_id=job_id)

    # Run job in celery
    # run_job_in_celery.delay(job_id)

    regular_service.process_job(job_id)

    return success_response(
        status_code=200,
        message='Job processing completed',
    )


