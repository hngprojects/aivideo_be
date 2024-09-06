from typing import Optional
from fastapi import Depends, Form, APIRouter, File, UploadFile, Request
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.v1.models.user import User
from api.v1.services.user import user_service
from api.utils.tool_limiter import track_tool_usage
from api.utils.success_response import success_response
from api.utils.files import upload_to_current_dir, contains_face
from api.v1.services.presets import preset_service
from api.v1.services.job import job_service
from api.v1.schemas.ai_tools.talking_avatar import TalkingHeadRequest
from api.v1.schemas.project import ProjectToolsEnum
from api.core.dependencies.celery.tasks.video_tasks import generate_talking_avatar_task


video_router = APIRouter(prefix="/tools/video", tags=["Tools"])

@video_router.post('/talking-head/image-upload', status_code=202, response_model=success_response)
@track_tool_usage(ProjectToolsEnum.image_to_video)
async def talking_head_image_upload(
    request: Request,
    script: str = Form(..., max_length=2500),
    aspect_ratio: str = Form(...),
    voice_over: str = Form(...),
    audio_id: Optional[str] = Form(None),
    file: UploadFile = File(...), 
    db: Session = Depends(get_db),
    user: User = Depends(user_service.get_current_user_optional)
):
    '''Endpoint to Talking Avatar'''

    file_extension = file.filename.split(".")[-1]
    image_file = await upload_to_current_dir(
        file, 
        allowed_extensions=['jpg', 'jpeg', 'png'],
        save_extension=file_extension,
        max_file_size=10 * 1024 * 1024
    )

    # Check if image contains a face
    # contains_face(image_file)
    
    if audio_id:
        audio = preset_service.fetch_music_by_id(
            db=db, music_id=audio_id
        )
        audio_file = audio.file_path

    task = generate_talking_avatar_task.apply_async(kwargs={
        'img_file': image_file,
        'audio_file': audio_file if audio_id else None,
        'aspect_ratio': aspect_ratio.lower(),
        'script': script,
        'voice_over': voice_over.lower(),
        'default': False
    })

    # Create project with job
    project = job_service.create_project_with_job(
        db=db,
        job=task,
        project_title='New project',
        project_type=ProjectToolsEnum.image_to_video.value,
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
@track_tool_usage(ProjectToolsEnum.talking_avatar)
async def talking_head_avatar_selection(
    request: Request,
    schema: TalkingHeadRequest,
    db: Session = Depends(get_db),
    user: User = Depends(user_service.get_current_user_optional)
):
    '''Endpoint to Talking Avatar'''

    avatar = preset_service.fetch_avatar_by_id(
        db=db, avatar_id=schema.avatar_id
    )

    if schema.audio_id:
        audio = preset_service.fetch_music_by_id(
            db=db, music_id=schema.audio_id
        )
        audio_file = audio.file_path

    image_file = avatar.file_path

    task = generate_talking_avatar_task.apply_async(kwargs={
        'img_file': image_file,
        'audio_file': audio_file if schema.audio_id else None,
        'aspect_ratio': schema.aspect_ratio.lower(),
        'script': schema.script,
        'voice_over': schema.voice_over.lower(),
        'default': True
    })

    # Create project with job
    project = job_service.create_project_with_job(
        db=db,
        job=task,
        project_title='New project',
        project_type=ProjectToolsEnum.talking_avatar.value,
    )

    return success_response(
        status_code=202,
        message="Talking Avatar generation task initiated successfully",
        data={
            "job_id": task.id,
            "project_id": project.id
        }
    )

