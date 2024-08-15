import asyncio
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from api.utils.websocket import manager
from api.v1.services.websocket import websocket_service
from api.v1.services.job import job_service

websocket_router = APIRouter(tags=['Websocket'])


@websocket_router.websocket("/ws/job/progress")
async def send_progress_report(websocket: WebSocket, job_id: str = Query(...)):
    '''Websocket endpoint to send real time progress reports on running jobs to the server'''

    await manager.connect(websocket)

    try:
        # Send job status updates if the job is in progress
        await websocket_service.send_job_status_updates(
            websocket=websocket, 
            job_id=job_id
        )

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logging.error(f"WebSocket error: {str(e)}")
        await websocket.close()
    finally:
        websocket.close()
