from fastapi import APIRouter, HTTPException
from celery.result import AsyncResult

from api.core.dependencies.celery.celery_app import worker
from api.v1.services.job import job_service
from api.utils.websocket import manager
from api.db.database import get_db


# background_router = APIRouter(prefix="/background-task", tags=["Background"])

# # This route is for database polling
# @background_router.get("/{task_id}/status")
# async def task_status(task_id: str):
#     task_result = AsyncResult(task_id, app=worker)
#     project = job_service.get_project_from_job(job_id=task_id)

#     status = task_result.state
#     result = None

#     if status == 'PENDING':
#         job_service.update_job(task_id, 'PENDING')

#     elif status == 'FAILURE':
#         result = str(task_result.info)
#         job_service.update_job(task_id, 'FAILURE', result)
#         raise HTTPException(status_code=400, detail=result)
    
#     elif status == 'SUCCESS':
#         result = task_result.result
#         job_service.update_job(task_id, 'SUCCESS', result)

#     else:
#         job_service.update_job(task_id, status)

#     return {"status": status, "result": result}


async def task_status(task_id: str):
    '''Function to send task status over websockets'''

    db = next(get_db())
    task_result = AsyncResult(task_id, app=worker)
    project = job_service.get_project_from_job(job_id=task_id)

    status = task_result.state
    result = None

    # Send WebSocket message with current status
    await manager.broadcast(f"Task {task_id}: Status is {status}")

    if status == 'PENDING':
        job_service.update_job(task_id, 'PENDING')

    elif status == 'FAILURE':
        result = str(task_result.info)
        job_service.update_job(task_id, 'FAILURE', result)
        await manager.broadcast(f"Task {task_id} failed with error: {result}")
        raise HTTPException(status_code=400, detail=result)
    
    elif status == 'SUCCESS':
        result = task_result.result
        job_service.update_job(task_id, 'SUCCESS', result)
        # Save project result
        project.result = result
        db.commit()
        await manager.broadcast(f"Task {task_id} completed successfully.")
        
    else:
        job_service.update_job(task_id, status)
