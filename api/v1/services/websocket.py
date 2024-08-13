from celery.result import AsyncResult
from fastapi import WebSocket

from api.db.database import get_db
from api.core.dependencies.celery.celery_app import worker
from api.v1.services.job import job_service
from api.utils.websocket import manager
from api.db.database import get_db

db = next(get_db())

class WebsocketService:

    async def send_job_status_updates(websocket: WebSocket, job_id: str):
        '''Function to send job status over websockets'''

        task_result = AsyncResult(job_id, app=worker)
        project = job_service.get_project_from_job(job_id=job_id)

        status = task_result.state
        result = None

        # Send WebSocket message with current status
        await manager.broadcast(f"Job {job_id}: Status is {status}")

        if status == 'PENDING':
            job_service.update_job(job_id, 'PENDING')

        elif status == 'FAILURE':
            result = str(task_result.info)
            job_service.update_job(job_id, 'FAILURE', result)
            await manager.broadcast(f"Job {job_id} failed with error: {result}")
            manager.disconnect(websocket)
        
        elif status == 'SUCCESS':
            result = task_result.result
            job_service.update_job(job_id, 'SUCCESS', result)

            # Save project result
            project.result = result
            db.commit()
            await manager.broadcast(f"Job {job_id} completed successfully.")
            manager.disconnect(websocket)
            
        else:
            job_service.update_job(job_id, status)


websocket_service = WebsocketService()
