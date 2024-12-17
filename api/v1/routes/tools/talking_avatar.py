from typing import Optional
from fastapi import Depends, Form, APIRouter, File, HTTPException, UploadFile, Request
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils import files
from api.utils import mime_types
from api.v1.models.user import User
from api.v1.services.user import user_service
from api.utils.tool_limiter import track_tool_usage
from api.utils.success_response import success_response
from api.v1.services.presets import preset_service
from api.v1.services.job import tifi_job_service
from api.v1.services.tools.general_video_service import video_service
from api.v1.schemas.tools.talking_avatar import TalkingHeadRequest
from api.v1.models.project import ProjectToolsEnum


video_router = APIRouter(prefix="/tools/video", tags=["Tools"])

@video_router.post('/talking-avatar/generate', status_code=202, response_model=success_response)
# @track_tool_usage(ProjectToolsEnum.image_to_video)
async def talking_head_image_upload(
    request: Request,
    script: str = Form(..., max_length=2500),
    aspect_ratio: str = Form('square'),
    bg_audio_id: Optional[str] = Form(None),
    custom_audio: Optional[UploadFile] = File(None),
    avatar_id: Optional[str] = Form(None),
    custom_avatar: Optional[UploadFile] = File(None),
    voice_id: Optional[str] = Form(None),
    custom_voice: Optional[UploadFile] = File(None),
    avatar_setting: Optional[str] = Form(None),
    # avatar_size: Optional[str] = Form('full'),
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(user_service.get_current_user_optional)
):
    '''Endpoint to Talking Avatar'''
    
    audio_url = None
    voice_url = None
    avatar_url = None
    
    # Validation checks
    if custom_audio and bg_audio_id:
        raise HTTPException(status_code=400, detail='Cannot use both custom audio and preset audio')
    
    if custom_voice and voice_id:
        raise HTTPException(status_code=400, detail='Cannot use both custom voice and preset voice')
    
    # if not custom_voice and not voice_id:
    #     raise HTTPException(status_code=400, detail='Cannot leave both custom voice and voice id empty')
    
    if custom_avatar and avatar_id:
        raise HTTPException(status_code=400, detail='Cannot use both custom avatar and preset avatar')
    
    if custom_avatar and not(voice_id or custom_voice):
        raise HTTPException(status_code=400, detail='Cannot use custom avatar without a voice selection')
    
    if avatar_id and voice_id:
        raise HTTPException(status_code=400, detail='Cannot select avatar and voice')
    
    # if avatar_size not in ['full', 'crop']:
    #     raise HTTPException(status_code=400, detail='Avatar size must be `full` or `crop` value')
    
    
    # Determine aspect ratio
    width, height = video_service.set_aspect_ratio(aspect_ratio.lower())
    
    if custom_audio:
        audio_url = await files.upload_audio_file(custom_audio)
    
    if custom_voice:
        voice_url = await files.upload_audio_file(custom_voice)
        
    if custom_avatar:
        avatar_url = await files.upload_image_file(custom_avatar)
        
    
    if avatar_id:
        avatar = preset_service.fetch_avatar_by_id(
            db=db, avatar_id=avatar_id
        )
        
        avatar_url = avatar.file_url
        voice_url = avatar.voice.file_url
    
    if bg_audio_id:
        audio = preset_service.fetch_music_by_id(
            db=db, music_id=bg_audio_id
        )
        # audio_file = audio.file_path
        audio_url = audio.file_url
        
    if voice_id:
        voice = preset_service.fetch_voice_by_id(
            db=db, voice_id=voice_id
        )
        voice_url = voice.file_url

    job = tifi_job_service.create(
        db=db,
        tool_name=ProjectToolsEnum.talking_avatar.value,
        payload={
            'image_url': avatar_url,
            'audio_url': audio_url,
            # 'aspect_ratio': aspect_ratio.lower(),
            'script': script,
            'voice_url': voice_url,
            'width': width,
            'height': height,
            'avatar_setting': avatar_setting,
            # 'avatar_size': avatar_size,
        },
        user_id=user.id if user else None,
        is_parallel=False
    )

    return success_response(
        status_code=202,
        message=f"{ProjectToolsEnum.talking_avatar.value} task initiated successfully",
        data={"job_id": job.id}
    )


# @video_router.post('/talking-head/avatar-selection', status_code=202, response_model=success_response)
# # @track_tool_usage(ProjectToolsEnum.talking_avatar)
# async def talking_head_avatar_selection(
#     request: Request,
#     schema: TalkingHeadRequest,
#     db: Session = Depends(get_db),
#     user: Optional[User] = Depends(user_service.get_current_user_optional)
# ):
#     '''Endpoint to Talking Avatar'''

#     avatar = preset_service.fetch_avatar_by_id(
#         db=db, avatar_id=schema.avatar_id
#     )

#     if schema.audio_id:
#         audio = preset_service.fetch_music_by_id(
#             db=db, music_id=schema.audio_id
#         )
#         audio_url = audio.file_url

#     image_url = avatar.file_url
    
#     job = tifi_job_service.create(
#         db=db,
#         tool_name=ProjectToolsEnum.talking_avatar.value,
#         payload={
#             'image_url': image_url,
#             'audio_url': audio_url if schema.audio_id else None,
#             'aspect_ratio': schema.aspect_ratio.lower(),
#             'script': schema.script,
#             'voice_over': avatar.gender.lower(),
#         },
#         user_id=user.id if user else None,
#         is_parallel=False,
#     )

#     return success_response(
#         status_code=202,
#         message=f"{ProjectToolsEnum.talking_avatar.value} task initiated successfully",
#         data={"job_id": job.id}
#     )
