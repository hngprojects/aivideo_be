"""Endpoints that handle video transcription and summarization"""

from typing import List, Optional
from fastapi import APIRouter, Depends, File, UploadFile, status, Request
from sqlalchemy.orm.session import Session

from api.db.database import get_db
from api.utils.files import delete_file, upload_files
from api.utils.logger import logging
from api.utils.success_response import success_response
from api.utils.tool_limiter import track_tool_usage
from api.v1.models.user import User
from api.v1.schemas.ai_tools.youtube import VideoLinkRequest, YTLinksRequest
from api.v1.models.project import ProjectToolsEnum
from api.v1.services.job import tifi_job_service
from api.v1.services.user import user_service
from api.utils.minio_service import minio_service


video_summary = APIRouter(prefix="/tools/summary", tags=["Tools"])

FILE_DIRECTORY = "summary_files"


@video_summary.post(
    "/batch-video-summarize",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=success_response
)
@track_tool_usage(ProjectToolsEnum.video_summarizer)
async def summarize_video_batch(
    request: Request,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(user_service.get_current_user_optional)
):
    """Enqueue a batch job to summarize a video"""

    uploaded_files = await upload_files(
        files,
        allowed_extensions=[
            '.mp4',
            '.avi',
            '.mkv',
            '.mov',
            '.wmv',
            '.flv',
            '.webm',
            '.m4v',
            '.3gp',
            '.mpeg',
            '.mpg'
        ],
        upload_folder=FILE_DIRECTORY,
        max_file_size=50 * 1024 * 1024,
        chunk_size=1024 * 1024
    )

    jobs = []

    for file in uploaded_files:
        # Upload video file to temporary stirage bucket
        video_url = minio_service.upload_to_tmp_bucket(source_file=file)
        delete_file(file)

        job = tifi_job_service.create(
            db=db,
            tool_name=ProjectToolsEnum.video_summarizer.value,
            payload={'video_url': video_url},
            user_id=user.id if user else None,
            is_parallel=False
        )

        jobs.append({
            "job_id": job.id,
            # "project_id": project.id,
        })
    return success_response(
        status_code=status.HTTP_202_ACCEPTED,
        message="Video summary generation task initiated successfully",
        data={
            "jobs": jobs
        }
    )


@video_summary.post(
    "/batch-youtube-summarize",
    status_code=status.HTTP_200_OK,
    response_model=success_response,
)
@track_tool_usage(ProjectToolsEnum.youtube_summarizer)
async def summarize_yt_vid(
    schema: YTLinksRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(user_service.get_current_user_optional)
):
    """Endpoint to download and summarize a single youtube video"""

    jobs = []
    for link in schema.links:
        job = tifi_job_service.create(
            db=db,
            tool_name=ProjectToolsEnum.youtube_summarizer.value,
            payload={'link': link},
            user_id=user.id if user else None,
            is_parallel=True
        )
        
        jobs.append({
            "job_id": job.id,
            # "project_id": project.id,
        })

    return success_response(
        status_code=202,
        message="Summary generation job initiated successfully",
        data={
            "jobs": jobs,
        },
    )



@video_summary.post(
    "/summarize-video",
    status_code=status.HTTP_200_OK,
    response_model=success_response,
)
@track_tool_usage(ProjectToolsEnum.video_summarizer)
async def summarize_up_vid(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(user_service.get_current_user_optional)
):
    """Endpoint to summarize a single video"""

    video = await upload_files(
        file,
        allowed_extensions=[
            ".mp4",
            ".avi",
            ".mkv",
            ".mov",
            ".wmv",
            ".flv",
            ".webm",
            ".m4v",
            ".3gp",
            ".mpeg",
            ".mpg",
        ],
        upload_folder="video_summary",
        max_file_size=50 * 1024 * 1024,
    )

    # Upload video file to temporary stirage bucket
    video_url = minio_service.upload_to_tmp_bucket(source_file=video[0])
    delete_file(video[0])

    job = tifi_job_service.create(
        db=db,
        tool_name=ProjectToolsEnum.video_summarizer.value,
        payload={'video_url': video_url},
        user_id=user.id if user else None,
        is_parallel=False
    )

    return success_response(
        status_code=202,
        message=f"{ProjectToolsEnum.video_summarizer.value} task initiated successfully",
        data={
            "job_id": job.id,
            # "project_id": project.id
        }
    )


@video_summary.post(
    "/summarize-youtube-video",
    status_code=status.HTTP_200_OK,
    response_model=success_response,
)
@track_tool_usage(ProjectToolsEnum.youtube_summarizer)
async def summarize_yt_vid(
    schema: VideoLinkRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(user_service.get_current_user_optional),
):
    """Endpoint to download and summarize a single youtube video"""

    job = tifi_job_service.create(
        db=db,
        tool_name=ProjectToolsEnum.youtube_summarizer.value,
        payload={'link': schema.link},
        user_id=user.id if user else None,
        is_parallel=True
    )

    return success_response(
        status_code=202,
        message=f"{ProjectToolsEnum.youtube_summarizer.value} task initiated successfully",
        data={
            "job_id": job.id,
            # "project_id": project.id
        }
    )
