from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from celery.result import AsyncResult

from api.utils.success_response import success_response
from api.core.dependencies.celery.celery_app import worker
from api.v1.services.job import job_service
from api.utils.websocket import manager
from api.db.database import get_db


background_router = APIRouter(prefix="/background", tags=["Background"])


@background_router.get("/job/{job_id}/status")
async def job_status(job_id: str):
    task_result = AsyncResult(job_id, app=worker)
    return {"status": task_result.state}


@background_router.get("/job/{job_id}/status")
async def send_job_status_updates(job_id: str, db: Session = Depends(get_db)):
    """Function to send job status over websockets"""

    task_result = AsyncResult(job_id, app=worker)
    project = job_service.get_project_from_job(job_id=job_id)

    status = task_result.state
    result = None

    project.is_active = False
    db.commit()

    if status == "PENDING":
        job_service.update_job(job_id, "Pending")

    elif status == "FAILURE":
        result = str(task_result.info)
        job_service.update_job(job_id, "Failed", result)

    elif status == "SUCCESS":
        result = task_result.result
        job_service.update_job(job_id, "Success", result)

        # Save project result
        project.result = result
        project.is_active = True
        db.commit()
    else:
        job_service.update_job(job_id, status)

    return success_response(
        status_code=200,
        message="Job progress retrieved",
        data={
            "job_id": job_id,
            "status": status,
        },
    )
