from typing import Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils.files import delete_file, upload_to_temp_dir
from api.utils.settings import settings
from api.utils.minio_service import minio_service
from api.utils.success_response import success_response
from api.utils.tool_limiter import track_tool_usage
from api.v1.models.project import ProjectToolsEnum
from api.v1.models.user import User
from api.v1.services.user import user_service
from api.v1.services.ffmpeg_tools import ffmpeg_service
from api.v1.services.job import tifi_job_service


ffmpeg_router = APIRouter(prefix="/tools/ffmpeg", tags=["Ffmpeg Tools"])


# Reusable across all routes for ffmpeg tools
async def upload_video_file(file):
    file_extension = file.filename.split(".")[-1]
    video_file = await upload_to_temp_dir(
        file, 
        allowed_extensions=[
            'mp4',
            'avi',
            'mkv',
            'mov',
            'wmv',
            'flv',
            'webm',
            'm4v',
            '3gp',
            'mpeg',
            'mpg'
        ],
        save_extension=file_extension,
        max_file_size=50 * 1024 * 1024
    )

    # Upload video file to temporary stirage bucket
    video_url = minio_service.upload_to_tmp_bucket(source_file=video_file)
    delete_file(video_file)

    return video_url


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
        max_file_size=10 * 1024 * 1024
    )

    # Upload video file to temporary stirage bucket
    image_url = minio_service.upload_to_tmp_bucket(source_file=image_file)
    delete_file(image_file)

    return image_url


@ffmpeg_router.post('/audio-extractor', status_code=202, response_model=success_response)
# @track_tool_usage(ProjectToolsEnum.audio_extractor)
async def extract_audio_from_video(
    request: Request,
    file: UploadFile = File(...),
    audio_extension: str = Form(default='mp3'),
    start_time: Optional[str] = Form(None),
    end_time: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(user_service.get_current_user_optional)
):
    '''Endpoint to extract the audio from a video'''

    if start_time:
        start_time_in_seconds = ffmpeg_service.time_to_seconds(start_time)
    if end_time:
        end_time_in_seconds = ffmpeg_service.time_to_seconds(end_time)
    
    if (start_time and end_time) and (start_time_in_seconds > end_time_in_seconds):
        raise HTTPException(status_code=400, detail="Start time must be less than or equal to end time")
    
    video_url = await upload_video_file(file)

    job = tifi_job_service.create(
        db=db,
        tool_name=ProjectToolsEnum.audio_extractor.value,
        payload={
            'video_url': video_url,
            'audio_extension': audio_extension.lower(),
            'start_time': start_time,
            'end_time': end_time,
        },
        user_id=user.id if user else None,
        is_parallel=False
    )

    return success_response(
        status_code=202,
        message=f"{ProjectToolsEnum.audio_extractor.value} task initiated successfully",
        data={"job_id": job.id}
    )


@ffmpeg_router.post('/resize-video', status_code=202, response_model=success_response)
# @track_tool_usage(ProjectToolsEnum.resize_video)
async def resize_video(
    request: Request,
    file: UploadFile = File(...),
    # aspect_ratio: str = Form(),
    width: int = Form(),
    height: int = Form(),
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(user_service.get_current_user_optional)
):
    '''Endpoint to resize a video'''

    video_url = await upload_video_file(file)

    job = tifi_job_service.create(
        db=db,
        tool_name=ProjectToolsEnum.resize_video.value,
        payload={
            'video_url': video_url,
            # 'aspect_ratio': aspect_ratio.lower(),
            'width': width,
            'height': height
        },
        user_id=user.id if user else None,
        is_parallel=False
    )

    return success_response(
        status_code=202,
        message=f"{ProjectToolsEnum.resize_video.value} task initiated successfully",
        data={"job_id": job.id}
    )


@ffmpeg_router.post('/compress-video', status_code=202, response_model=success_response)
# @track_tool_usage(ProjectToolsEnum.video_compressor)
async def compress_video(
    request: Request,
    file: UploadFile = File(...),
    compression_speed: str = Form(default='medium'),
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(user_service.get_current_user_optional)
):
    '''Endpoint to compress a video'''

    video_url = await upload_video_file(file)

    job = tifi_job_service.create(
        db=db,
        tool_name=ProjectToolsEnum.video_compressor.value,
        payload={
            'video_url': video_url,
            'compression_speed': compression_speed.lower()
        },
        user_id=user.id if user else None,
        is_parallel=False
    )

    return success_response(
        status_code=202,
        message=f"{ProjectToolsEnum.video_compressor.value} task initiated successfully",
        data={"job_id": job.id}
    )


@ffmpeg_router.post('/create-gif', status_code=202, response_model=success_response)
# @track_tool_usage(ProjectToolsEnum.gif_creator)
async def create_gif_from_video(
    request: Request,
    file: UploadFile = File(...),
    start_time: int = Form(default=0),
    gif_duration: int = Form(default=5),
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(user_service.get_current_user_optional)
):
    '''Endpoint to create gif from a video'''

    video_url = await upload_video_file(file)

    job = tifi_job_service.create(
        db=db,
        tool_name=ProjectToolsEnum.gif_creator.value,
        payload={
            'video_url': video_url,
            'start_time': start_time,
            'duration': gif_duration,
        },
        user_id=user.id if user else None,
        is_parallel=False
    )

    return success_response(
        status_code=202,
        message=f"{ProjectToolsEnum.gif_creator.value} task initiated successfully",
        data={"job_id": job.id}
    )


@ffmpeg_router.post('/add-watermark-to-video', status_code=202, response_model=success_response)
# @track_tool_usage(ProjectToolsEnum.video_watermarker)
async def add_watermark_to_video(
    request: Request,
    video_file: UploadFile = File(...),
    watermark_image_file: UploadFile = File(...),
    position: str = Form(default='top-right'),
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(user_service.get_current_user_optional)
):
    '''Endpoint to add watermark a video'''

    video_url = await upload_video_file(video_file)
    watermark_image_url = await upload_image_file(watermark_image_file)

    job = tifi_job_service.create(
        db=db,
        tool_name=ProjectToolsEnum.video_watermarker.value,
        payload={
            'video_url': video_url,
            'watermark_image_url': watermark_image_url,
            'position': position,
        },
        user_id=user.id if user else None,
        is_parallel=False
    )

    return success_response(
        status_code=202,
        message=f"{ProjectToolsEnum.video_watermarker.value} task initiated successfully",
        data={"job_id": job.id}
    )
