"""Endpoints that handle video transcription and summarization"""

from typing import List, Optional
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status, Request, Form
from sqlalchemy.orm.session import Session

from api.db.database import get_db
from api.utils.files import delete_file, upload_multiple_files_to_tmp_dir, upload_to_temp_dir
from api.utils.success_response import success_response
from api.utils.tool_limiter import track_tool_usage
from api.v1.models.user import User
from api.v1.schemas.tools.youtube import VideoLinkRequest, YTLinksRequest
from api.v1.models.project import ProjectToolsEnum
from api.v1.services.job import tifi_job_service
from api.v1.services.user import user_service
from api.utils.minio_service import minio_service
from api.v1.routes.tools.summary import check_detail_level


video_summary = APIRouter(prefix="/tools/summary", tags=["Tools"])

@video_summary.post(
    "/batch-video-summarize",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=success_response
)
# @track_tool_usage(ProjectToolsEnum.youtube_video_summarizer)
async def batch_summarize_video(
    request: Request,
    files: List[UploadFile] = File(...),
    detail_level: str = Form(default='short'),
    db: Session = Depends(get_db),
    user: User = Depends(user_service.get_current_user)
):
    """Enqueue a batch job to summarize a video"""

    check_detail_level(detail_level)

    uploaded_files = await upload_multiple_files_to_tmp_dir(
        files,
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
        max_file_size=195,
        save_extension='mp4'
    )

    video_urls = []

    # Upload all video files to temporary stirage bucket
    for file in uploaded_files:
        video_url = minio_service.upload_to_tmp_bucket(source_file=file)
        video_urls.append(video_url)
        delete_file(file)

    job = tifi_job_service.create(
        db=db,
        tool_name=ProjectToolsEnum.youtube_video_summarizer.value,
        payload={
            'links': video_urls, 
            'batch': True, 
            'type': 'video',
            'detail_level': detail_level.lower()
        },
        user_id=user.id if user else None,
        is_parallel=False
    )

    return success_response(
        status_code=status.HTTP_202_ACCEPTED,
        message=f"{ProjectToolsEnum.youtube_video_summarizer.value} task initiated successfully",
        data={"job_id": job.id}
    )


@video_summary.post(
    "/batch-youtube-summarize",
    status_code=status.HTTP_200_OK,
    response_model=success_response,
)
# @track_tool_usage(ProjectToolsEnum.youtube_video_summarizer)
async def batch_summarize_youtube_video(
    schema: YTLinksRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(user_service.get_current_user)
):
    """Endpoint to download and summarize a single youtube video"""

    check_detail_level(schema.detail_level)

    job = tifi_job_service.create(
        db=db,
        tool_name=ProjectToolsEnum.youtube_video_summarizer.value,
        payload={
            'links': schema.links, 
            'batch': True, 
            'type': 'youtube',
            'detail_level': schema.detail_level.lower()
        },
        user_id=user.id if user else None,
        is_parallel=False
    )

    return success_response(
        status_code=202,
        message=f"{ProjectToolsEnum.youtube_video_summarizer.value} task initiated successfully",
        data={'job_id': job.id}
    )


@video_summary.post(
    "/summarize-video",
    status_code=status.HTTP_200_OK,
    response_model=success_response,
)
# @track_tool_usage(ProjectToolsEnum.youtube_video_summarizer)
async def summarize_video(
    request: Request,
    file: UploadFile = File(...),
    detail_level: str = Form(default='short'),
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(user_service.get_current_user_optional)
):
    """Endpoint to summarize a single video"""

    check_detail_level(detail_level)

    video_file = await upload_to_temp_dir(
        file,
        allowed_extensions=[
            "mp4",
            "avi",
            "mkv",
            "mov",
            "wmv",
            "flv",
            "webm",
            "m4v",
            "3gp",
            "mpeg",
            "mpg",
        ],
        save_extension="mp4",
        max_file_size=195,
    )

    # Upload video file to temporary stirage bucket
    video_url = minio_service.upload_to_tmp_bucket(source_file=video_file)
    delete_file(video_file)

    job = tifi_job_service.create(
        db=db,
        tool_name=ProjectToolsEnum.youtube_video_summarizer.value,
        payload={
            'links': [video_url], 
            'batch': False, 
            'type': 'video',
            'detail_level': detail_level.lower()
        },
        user_id=user.id if user else None,
        is_parallel=False
    )

    return success_response(
        status_code=202,
        message=f"{ProjectToolsEnum.youtube_video_summarizer.value} task initiated successfully",
        data={"job_id": job.id}
    )


@video_summary.post(
    "/summarize-youtube-video",
    status_code=status.HTTP_200_OK,
    response_model=success_response,
)
# @track_tool_usage(ProjectToolsEnum.youtube_video_summarizer)
async def summarize_youtube_video(
    schema: VideoLinkRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(user_service.get_current_user_optional),
):
    """Endpoint to download and summarize a single youtube video"""

    check_detail_level(schema.detail_level)

    job = tifi_job_service.create(
        db=db,
        tool_name=ProjectToolsEnum.youtube_video_summarizer.value,
        payload={
            'links': [schema.link], 
            'batch': False, 
            'type': 'youtube',
            'detail_level': schema.detail_level.lower()
        },
        user_id=user.id if user else None,
        is_parallel=False
    )

    return success_response(
        status_code=202,
        message=f"{ProjectToolsEnum.youtube_video_summarizer.value} task initiated successfully",
        data={"job_id": job.id}
    )
