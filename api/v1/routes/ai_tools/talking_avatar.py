from fastapi import Depends, Form, APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import requests

from api.db.database import get_db
from api.utils.success_response import success_response
from api.utils.files import upload_file_to_current_dir
from api.v1.services.presets import preset_service
from api.v1.services.job import job_service
from api.v1.schemas.ai_tools.talking_avatar import DownloadRequest, TalkingHeadRequest
from api.core.dependencies.celery.tasks.video_tasks import generate_talking_avatar_task

video_router = APIRouter(prefix="/tools/video", tags=["Tools"])

@video_router.post('/talking-head/image-upload', status_code=202, response_model=success_response)
async def talking_head_image_upload(
    script: str = Form(...),
    aspect_ratio: str = Form(...),
    voice_over: str = Form(...),
    audio_id: str = Form(...),
    file: UploadFile = File(...), 
    db: Session = Depends(get_db)
):
    '''Endpoint to Talking Avatar'''

    file_extension = file.filename.split(".")[-1]
    image_file = await upload_file_to_current_dir(
        file, 
        allowed_extensions=['jpg', 'jpeg', 'png'],
        save_extension=file_extension,
        max_file_size=10 * 1024 * 1024
    )

    audio = preset_service.fetch_music_by_id(
        db=db, music_id=audio_id
    )

    audio_file = audio.file_path

    task = generate_talking_avatar_task.apply_async(kwargs={
        'img_file': image_file,
        'audio_file': audio_file,
        'aspect_ratio': aspect_ratio,
        'script': script,
        'voice_over': voice_over.lower(),
        'default': False
    })

    # Create project with job
    project = job_service.create_project_with_job(
        job=task,
        project_title='New project',
        project_type='Talking Head',
        # user_id = pass in the current user id for authenticated users
    )

    return success_response(
        status_code=202,
        message="Talking Avatar generation task initiated successfully",
        data={
            "job_id": task.id,
            "project_id": project.id
        }
    )


@video_router.post('/talking-head/avatar-selection', status_code=202, response_model=success_response)
async def talking_head_avatar_selection(
    schema: TalkingHeadRequest,
    db: Session = Depends(get_db)
):
    '''Endpoint to Talking Avatar'''

    avatar = preset_service.fetch_avatar_by_id(
        db=db, avatar_id=schema.avatar_id
    )

    audio = preset_service.fetch_music_by_id(
        db=db, music_id=schema.audio_id
    )

    image_file = avatar.file_path
    audio_file = audio.file_path

    task = generate_talking_avatar_task.apply_async(kwargs={
        'img_file': image_file,
        'audio_file': audio_file,
        'aspect_ratio': schema.aspect_ratio.lower(),
        'script': schema.script,
        'voice_over': schema.voice_over.lower(),
        'default': True
    })

    # Create project with job
    project = job_service.create_project_with_job(
        job=task,
        project_title='New project',
        project_type='Talking Head',
        # user_id = pass in the current user id for authenticated users
    )

    return success_response(
        status_code=202,
        message="Talking Avatar generation task initiated successfully",
        data={
            "job_id": task.id,
            "project_id": project.id
        }
    )


@video_router.post("/download")
async def download_video(schema: DownloadRequest):
    try:
        # Fetch the video from the URL
        response = requests.get(schema.file_url, stream=True)
        response.raise_for_status()  # Check for errors in the response

        video_filename = "downloaded_video.mp4"
        with open(video_filename, "wb") as video_file:
            video_file.write(response.content)

        # Return the video file as a FileResponse
        return FileResponse(video_filename, media_type="video/mp4", filename="convey-talking-avatar-video.mp4")

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Error downloading video: {str(e)}")
