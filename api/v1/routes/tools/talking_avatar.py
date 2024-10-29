from typing import Optional
from fastapi import Depends, Form, APIRouter, File, UploadFile, Request
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils.minio_service import minio_service
from api.utils import mime_types
from api.v1.models.user import User
from api.v1.services.user import user_service
from api.utils.tool_limiter import track_tool_usage
from api.utils.success_response import success_response
from api.utils.files import delete_file, upload_to_temp_dir, contains_face
from api.v1.services.presets import preset_service
from api.v1.services.job import tifi_job_service
from api.v1.schemas.tools.talking_avatar import TalkingHeadRequest
from api.v1.models.project import ProjectToolsEnum


video_router = APIRouter(prefix="/tools/video", tags=["Tools"])

@video_router.post('/talking-head/image-upload', status_code=202, response_model=success_response)
# @track_tool_usage(ProjectToolsEnum.image_to_video)
async def talking_head_image_upload(
    request: Request,
    script: str = Form(..., max_length=2500),
    aspect_ratio: str = Form(...),
    voice_over: str = Form(...),
    audio_id: Optional[str] = Form(None),
    file: UploadFile = File(...), 
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(user_service.get_current_user_optional)
):
    '''Endpoint to Talking Avatar'''

    file_extension = file.filename.split(".")[-1]
    image_file = await upload_to_temp_dir(
        file, 
        allowed_extensions=['jpg', 'jpeg', 'png'],
        save_extension=file_extension,
        max_file_size=20
    )

    # Check if image contains a face
    # contains_face(image_file)

    # Upload image to minio and delete the file
    image_url = minio_service.upload_to_tmp_bucket(source_file=image_file)
    # Delete image file
    delete_file(image_file)
    
    if audio_id:
        audio = preset_service.fetch_music_by_id(
            db=db, music_id=audio_id
        )
        # audio_file = audio.file_path
        audio_url = audio.file_url

    job = tifi_job_service.create(
        db=db,
        tool_name=ProjectToolsEnum.talking_avatar.value,
        payload={
            'image_url': image_url,
            'audio_url': audio_url if audio_id else None,
            'aspect_ratio': aspect_ratio.lower(),
            'script': script,
            'voice_over': voice_over.lower(),
        },
        user_id=user.id if user else None,
        is_parallel=False
    )

    return success_response(
        status_code=202,
        message=f"{ProjectToolsEnum.talking_avatar.value} task initiated successfully",
        data={"job_id": job.id}
    )


@video_router.post('/talking-head/avatar-selection', status_code=202, response_model=success_response)
# @track_tool_usage(ProjectToolsEnum.talking_avatar)
async def talking_head_avatar_selection(
    request: Request,
    schema: TalkingHeadRequest,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(user_service.get_current_user_optional)
):
    '''Endpoint to Talking Avatar'''

    avatar = preset_service.fetch_avatar_by_id(
        db=db, avatar_id=schema.avatar_id
    )

    if schema.audio_id:
        audio = preset_service.fetch_music_by_id(
            db=db, music_id=schema.audio_id
        )
        audio_url = audio.file_url

    image_url = avatar.file_url
    
    job = tifi_job_service.create(
        db=db,
        tool_name=ProjectToolsEnum.talking_avatar.value,
        payload={
            'image_url': image_url,
            'audio_url': audio_url if schema.audio_id else None,
            'aspect_ratio': schema.aspect_ratio.lower(),
            'script': schema.script,
            'voice_over': avatar.gender.lower(),
        },
        user_id=user.id if user else None,
        is_parallel=False,
    )

    return success_response(
        status_code=202,
        message=f"{ProjectToolsEnum.talking_avatar.value} task initiated successfully",
        data={"job_id": job.id}
    )
