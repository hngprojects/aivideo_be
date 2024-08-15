from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, WebSocket
from sqlalchemy.orm import Session
from api.db.database import get_db
from api.v1.services.video import video_service
from api.v1.services.job import job_service
from api.core.dependencies.celery.tasks.video_task import generate_video_task
from api.utils.websocket import manager

video_router = APIRouter(prefix='/video', tags=['Video'])

@video_router.post('/generate')
async def generate_video(text_prompt: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Endpoint to initiate video generation"""
    
    # Define video parameters
    width = 1344
    height = 768
    motion = 5
    seed = 0
    upscale = True
    interpolate = True
    
    # Run the task
    task = generate_video_task.delay(text_prompt, width, height, motion, seed, upscale, interpolate)
    
    # Create a project and associate with the job
    project = job_service.create_project_with_job(
        job=task,
        project_title='New Video Generation Project',
        project_type='Video Generation'
    )
    
    return {"job_id": task.id, "project_id": project.id}

@video_router.get('/status/{task_id}')
async def video_status(task_id: str):
    """Endpoint to check the status of the video generation"""
    
    task_result = generate_video_task.AsyncResult(task_id)
    status = task_result.state
    result = None
    
    if status == 'FAILURE':
        result = str(task_result.info)
        raise HTTPException(status_code=400, detail=result)
    
    elif status == 'SUCCESS':
        result = task_result.result
    
    return {"status": status, "result": result}
