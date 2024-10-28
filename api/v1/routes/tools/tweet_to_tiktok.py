from typing import Optional
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


tweet_to_tiktok_router = APIRouter(prefix="/tools/tweet-to-tiktok", tags=["Tools"])

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
    '/generate-video', 
    status_code=202, 
    response_model=success_response
)
# @track_tool_usage(ProjectToolsEnum.tweet_to_tiktok)
async def convert_tweet_to_video(
    schema: TweetToTiktokRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(user_service.get_current_user_optional)
):
    '''Endpoint to convert a script to video'''
    
    if schema.tweet_link and schema.text:
        raise HTTPException(status_code=400, detail='Cannot have both text and tweet links')
    
    if not schema.text and not schema.tweet_link:
        raise HTTPException(status_code=400, detail='Must provide either text or tweet link')
    
    if schema.audio_id:
        audio = preset_service.fetch_music_by_id(
            db=db, music_id=schema.audio_id
        )
        audio_url = audio.file_url
    
    if schema.tweet_link:
        # TODO: Get tweet text from tweet link
        schema.text = ''
        
    job = tifi_job_service.create(
        db=db,
        tool_name=ProjectToolsEnum.tweet_to_tiktok.value,
        payload={
            'text': schema.text,
            'scene_media_urls': schema.scene_media_urls,
            'bg_audio_url': audio_url if schema.audio_id else None,
            'voice_over': schema.voice_over.lower(),
            'video_style': schema.video_style.lower(),
        },
        user_id=user.id if user else None,
        is_parallel=False
    )
    
    return success_response(
        status_code=202,
        message=f"{ProjectToolsEnum.tweet_to_tiktok.value} task initiated successfully",
        data={'job_id': job.id}
    )
