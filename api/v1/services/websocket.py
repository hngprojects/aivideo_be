from celery.result import AsyncResult
from fastapi import WebSocket

from api.db.database import get_db
from api.core.dependencies.celery.celery_app import worker
from api.v1.services.job import job_service
from api.utils.websocket import manager
from api.db.database import get_db

db = next(get_db())

class WebsocketService:

    async def send_job_status_updates(self, websocket: WebSocket, job_id: str):
        '''Function to send job status over websockets'''

        while True:
            task_result = AsyncResult(job_id, app=worker)
            project = job_service.get_project_from_job(job_id=job_id)

            status = task_result.state
            result = None

            # Send WebSocket message with current status
            await manager.send_message(
                message=f"Job {job_id}: Status is {status}",
                websocket=websocket
            )

            project.is_active = False
            db.commit()

            if status == 'PENDING':
                job_service.update_job(job_id, 'PENDING')

            elif status == 'FAILURE':
                result = str(task_result.info)
                job_service.update_job(job_id, 'FAILURE', result)

                # Send message
                await manager.send_message(
                    message=f"Job {job_id} failed with error: {result}",
                    websocket=websocket
                )
                break
            
            elif status == 'SUCCESS':
                result = task_result.result
                job_service.update_job(job_id, 'SUCCESS', result)

                # Save project result
                project.result = result
                project.is_active = True
                db.commit()

                # Send message
                await manager.send_message(
                    message=f"Job {job_id} completed successfully.",
                    websocket=websocket
                )
                break
                
            else:
                job_service.update_job(job_id, status)


websocket_service = WebsocketService()
