from typing import List, Optional
from fastapi import Depends, Form, APIRouter, File, HTTPException, Query, UploadFile, Request
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils.minio_service import minio_service
from api.utils.stock_media_service import StockMediaService
from api.utils import mime_types
from api.v1.models.user import User
from api.v1.services.user import user_service
from api.utils.tool_limiter import track_tool_usage
from api.utils.success_response import success_response
from api.utils.files import delete_file, upload_to_temp_dir, contains_face
from api.v1.services.job import tifi_job_service
from api.v1.services.presets import preset_service
from api.v1.schemas.tools.tweet_to_tiktok import SceneGeneration, TweetToTiktokRequest
from api.v1.services.tools.tweet_to_tiktok import tweet_to_tiktok_service
from api.v1.models.project import ProjectToolsEnum


tweet_to_tiktok_router = APIRouter(prefix="/tools", tags=["Tools"])


async def upload_audio_file(file):
    file_extension = file.filename.split(".")[-1]
    audio_file = await upload_to_temp_dir(
        file, 
        allowed_extensions=[
            'mp3',
            'wav',
        ],
        save_extension=file_extension,
        max_file_size=50
    )

    # Upload video file to temporary stirage bucket
    audio_file = minio_service.upload_to_tmp_bucket(source_file=audio_file)
    delete_file(audio_file)

    return audio_file

async def upload_image_file(file):
    file_extension = file.filename.split(".")[-1]
    image_file = await upload_to_temp_dir(
        file, 
        allowed_extensions=[
            'jpg',
            'png',
            'jpeg',
            'jfif'
        ],
        save_extension=file_extension,
        max_file_size=20
    )

    # Upload video file to temporary stirage bucket
    image_url = minio_service.upload_to_tmp_bucket(source_file=image_file)
    delete_file(image_file)

    return image_url


@tweet_to_tiktok_router.post('/generate-scenes', status_code=200)
async def generate_scenes(
    schema: SceneGeneration,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(user_service.get_current_user_optional)
):
    '''Endpoint to generate scenes descriptions from a script'''
    
    scenes = tweet_to_tiktok_service.generate_scene_descriptions(schema.script)
    
    return success_response(
        status_code=200,
        message="Generated scene descriptions successfully",
        data={"scenes": scenes}
    )


@tweet_to_tiktok_router.post(
    '/tweet-to-tiktok/generate-video', 
    status_code=202, 
    response_model=success_response
)
# @track_tool_usage(ProjectToolsEnum.tweet_to_tiktok)
async def convert_tweet_to_video(
    # schema: TweetToTiktokRequest,
    request: Request,
    db: Session = Depends(get_db),
    text: Optional[str] = Form(None),
    tweet_link: Optional[str] = Form(None),
    avatar_id: Optional[str] = Form(None),
    custom_avatar: Optional[UploadFile] = File(None),
    background_audio_id: Optional[str] = Form(None),
    custom_audio: Optional[UploadFile] = File(None),
    voice_id: Optional[str] = Form(None),
    custom_voice: Optional[UploadFile] = File(None),
    scene_media_urls: List[str] = Form(...),
    video_style: str = Form(...),
    user: Optional[User] = Depends(user_service.get_current_user_optional)
):
    '''Endpoint to convert a script to video'''
    
    bg_audio_url = None
    voice_url = None
    avatar_url = None
    
    if tweet_link and text:
        raise HTTPException(status_code=400, detail='Cannot have both text and tweet links')
    
    if not text and not tweet_link:
        raise HTTPException(status_code=400, detail='Must provide either text or tweet link')
    
    if custom_audio and background_audio_id:
        raise HTTPException(status_code=400, detail='Cannot use both custom audio and preset audio')
    
    if custom_voice and voice_id:
        raise HTTPException(status_code=400, detail='Cannot use both custom voice and preset voice')
    
    if not custom_voice and not voice_id:
        raise HTTPException(status_code=400, detail='Cannot leave both custom voice and voice id empty')
    
    if custom_avatar and avatar_id:
        raise HTTPException(status_code=400, detail='Cannot use both custom avatar and preset avatar')
    
    if custom_avatar and (not voice_id or not custom_voice):
        raise HTTPException(status_code=400, detail='Cannot use custom avatar without a voice selection')
    
    
    # -----------------------------------------------------------
    
    if background_audio_id:
        audio = preset_service.fetch_music_by_id(
            db=db, music_id=background_audio_id
        )
        bg_audio_url = audio.file_url
    
    if voice_id:
        voice = preset_service.fetch_voice_by_id(
            db=db, voice_id=voice_id
        )
        voice_url = voice.file_url
    
    if avatar_id:
        avatar = preset_service.fetch_avatar_by_id(
            db=db, avatar_id=avatar_id
        )
        avatar_url = avatar.file_url
        voice_url = avatar.voice.file_url
    
    if custom_audio:
        bg_audio_url = await upload_audio_file(custom_audio)
    
    if custom_voice:
        voice_url = await upload_audio_file(custom_voice)
        
    if custom_avatar:
        avatar_url = await upload_image_file(custom_avatar)
    
    if tweet_link:
        # TODO: Get tweet text from tweet link
        text = ''
        
    job = tifi_job_service.create(
        db=db,
        tool_name=ProjectToolsEnum.tweet_to_tiktok.value,
        payload={
            'text': text,
            'scene_media_urls': scene_media_urls,
            'bg_audio_url': bg_audio_url,
            # 'voice_over': voice_over.lower(),
            'voice_url': voice_url,
            'avatar_image_url': avatar_url,
            'video_style': video_style.lower(),
        },
        user_id=user.id if user else None,
        is_parallel=False
    )
    
    return success_response(
        status_code=202,
        message=f"{ProjectToolsEnum.tweet_to_tiktok.value} task initiated successfully",
        data={'job_id': job.id}
    )
