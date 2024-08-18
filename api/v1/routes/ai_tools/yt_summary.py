from fastapi import APIRouter, Depends, File, UploadFile, status, Request
from sqlalchemy.orm import Session

from api.core.dependencies.celery.tasks.video_summary_tasks import (
    generate_video_summary_task,
    download_and_generate_video_summmary_task,
)
from api.db.database import get_db
from api.utils.logger import logging
from api.utils.pdf_transform import pdf_transform
from api.utils.success_response import success_response
from api.utils.transcriber import transcribe
from api.utils.videos import upload_video
from api.utils.ytdownload import download_video
from api.v1.services.job import job_service
from api.v1.schemas.ai_tools.youtube import VideoLinkRequest
from api.utils.files import convert_video_to_audio, delete_file
from api.v1.services.ai_tools.youtube_summarizer import transcription_service
from api.core.dependencies.celery.celery_app import worker
from api.db.database import get_db
import json
from api.utils.ytdownload import download_video
import time
import os
from api.utils.files import upload_files
from api.v1.services.ai_tools.summary import summary_service

yt_summary = APIRouter(prefix="/tools/summary", tags=["Tools"])


@yt_summary.post(
    "/video",
    status_code=status.HTTP_200_OK,
    # response_model=success_response,
)
async def summarize_up_vid(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Endpoint to summarize a single video"""
    FILE_DIRECTORY = "summary_files"
    video = await upload_files(
        file, allowed_extensions=["mp4", "mp3"], upload_folder=FILE_DIRECTORY
    )
    task = generate_video_summary_task.delay(video[0])
    logging.info(f"Background task started {task.id}")
    # Create project with job
    project = job_service.create_project_with_job(
        job=task, project_title="New project", project_type="YT video Summarizer"
    )

    return success_response(
        status_code=202,
        message="Summary generation job initiated successfully",
        data={
            "job_id": task.id,
            "project_id": project.id,
        },
    )


@yt_summary.post(
    "/youtube",
    status_code=status.HTTP_200_OK,
    response_model=success_response,
)
async def summarize_yt_vid(request: VideoLinkRequest, db: Session = Depends(get_db)):
    """Endpoint to download and summarize a single youtube video"""

    task = download_and_generate_video_summmary_task.delay(request.link)
    logging.info(f"Background task started {task.id}")
    # Create project with job
    project = job_service.create_project_with_job(
        job=task, project_title="New project", project_type="YT video Summarizer"
    )

    return success_response(
        status_code=202,
        message="Summary generation job initiated successfully",
        data={
            "job_id": task.id,
            "project_id": project.id,
        },
    )
