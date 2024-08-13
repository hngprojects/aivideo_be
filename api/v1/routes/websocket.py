from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from api.utils.websocket import manager
from api.v1.services.websocket import websocket_service

websocket_router = APIRouter(tags=['Websocket'])


@websocket_router.websocket("/ws/job/progress")
async def send_progress_report(websocket: WebSocket, job_id: str = Query(...)):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"Message text was: {data}")

            # Send task_status_updates
            await websocket_service.send_job_status_updates(job_id)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
