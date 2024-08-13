from fastapi import APIRouter, HTTPException
from celery.result import AsyncResult

from api.core.dependencies.celery.celery_app import worker
from api.v1.services.celery import celery_service


background_router = APIRouter(prefix="/background-task", tags=["Background"])

# This route is for database polling
@background_router.get("/{task_id}/status")
async def task_status(task_id: str):
    task_result = AsyncResult(task_id, app=worker)
    status = task_result.state
    result = None

    if status == 'PENDING':
        celery_service.update_task(task_id, 'PENDING')
    elif status == 'FAILURE':
        result = str(task_result.info)
        celery_service.update_task(task_id, 'FAILURE', result)
        raise HTTPException(status_code=400, detail=result)
    elif status == 'SUCCESS':
        result = task_result.result
        celery_service.update_task(task_id, 'SUCCESS', result)
    else:
        celery_service.update_task(task_id, status)

    return {"status": status, "result": result}