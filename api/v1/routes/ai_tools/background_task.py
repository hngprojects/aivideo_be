from fastapi import APIRouter
from celery.result import AsyncResult

from api.utils.success_response import success_response
from api.core.dependencies.celery.celery_app import worker

background_router = APIRouter(prefix="/background", tags=["Background"])

@background_router.get("/task/{task_id}/status")
async def task_status(task_id: str):
    task_result = AsyncResult(task_id, app=worker)
    return {"status": task_result.state}
