from fastapi import APIRouter, File, UploadFile, HTTPException, Request, Body, Form
from api.core.dependencies.celery.tasks.video_tasks import (
    upload_video_task,
    generate_thumbnails_task,
    select_and_download_thumbnail_task,
    process_youtube_video_task,
)
from api.utils.settings import settings
from api.utils.success_response import success_response
from api.utils.files import upload_file
from api.v1.services.job import job_service
from api.v1.schemas.ai_tools.thumbnail import ThumbnailRequest, ThumbnailSelectionRequest
from urllib.parse import urljoin
import os
import json

thumbnail_router = APIRouter(
    prefix="/tools/thumbnail-generator", tags=["Tools"])
max_file_size = 100 * 1024 * 1024  # 100 MB

@thumbnail_router.post("/upload-or-process")
async def upload_or_process_video(
    request: Request,
    file: UploadFile = File(None),
    youtube_url: str = Form(None)
):
    base_url = str(request.base_url)
    video_id = None
    task_id = None

    if file:
        file_content = await file.read()
        file_size = len(file_content)
        await file.seek(0)

        if file_size > max_file_size:
            raise HTTPException(
                status_code=400, detail="File exceeds the maximum allowed size of 100MB."
            )

        saved_path = await upload_file(
            file,
            allowed_extensions=settings.ALLOWED_EXTENSIONS,
            upload_folder='videos',
            save_extension=file.filename.split('.')[-1].lower(),
        )

        video_id = os.path.basename(saved_path).split('.')[0]
        task = upload_video_task.delay(video_id, base_url)
        task_id = task.id

    elif youtube_url:
        task = process_youtube_video_task.delay(youtube_url, base_url)
        task_id = task.id

        
        try:
            result = task.get(timeout=120)  
            response_data = json.loads(result)
            video_id = response_data.get('video_id')
            # video_size = response_data.get('video_size')

            # if video_size > max_file_size:
            #     raise HTTPException(
            #         status_code=400, detail="YouTube video exceeds the maximum allowed size of 100MB."
            #     )

        except HTTPException as e:
            raise e  
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to download YouTube video: {str(e)}"
            )

    else:
        raise HTTPException(
            status_code=400, detail="Either file or YouTube URL must be provided."
        )

    if not video_id:
        raise HTTPException(
            status_code=500, detail="Failed to process video."
        )

    project = job_service.create_project_with_job(
        job=task,
        project_title='Video Processing and Thumbnail Generation',
        project_type='Video Thumbnail Generator'
    )

    return success_response(
        status_code=200,
        message="Video processing started successfully.",
        data={
            "job_id": task_id,
            "project_id": project.id,
            
        }
    )

@thumbnail_router.post("/generate-thumbnails")
async def generate_thumbnails(
    request: Request,
    video_id: str = Form(...),
    timestamp: float = Form(None)  
):
    base_url = str(request.base_url)

    if not video_id:
        raise HTTPException(
            status_code=400, detail="Video ID is required."
        )
    
    
    task_title = 'Manual Thumbnail Capture' if timestamp is not None else 'Auto Thumbnail Generation'

    
    if timestamp is not None:
       
        task = generate_thumbnails_task.delay(video_id, base_url, timestamp=timestamp)
    else:
        
        task = generate_thumbnails_task.delay(video_id, base_url)

    project = job_service.create_project_with_job(
        job=task,
        project_title=task_title,
        project_type='Video Thumbnail Generator'
    )

    return success_response(
        status_code=200,
        message=f"{task_title} started successfully.",
        data={
            "job_id": task.id,
            "project_id": project.id,
           
        }
    )

@thumbnail_router.post("/select-thumbnail/{video_id}")
async def select_and_download_thumbnail(
    request: Request,
    video_id: str,
    body: ThumbnailSelectionRequest
):
    task = select_and_download_thumbnail_task.delay(
        video_id, body.thumbnail_id, body.resolution, str(request.url)
    )

    project = job_service.create_project_with_job(
        job=task,
        project_title='Thumbnail Selection and Download',
        project_type='Video Thumbnail Generator'
    )

    return success_response(
        status_code=200,
        message="Thumbnail selection and download started successfully.",
        data={
            "job_id": task.id,
            "project_id": project.id
        }
    )
