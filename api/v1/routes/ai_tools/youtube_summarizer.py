#!/usr/bin/env python3
"""Endpoints that handle video transcription and summarization"""
from typing import List

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm.session import Session

from api.core.dependencies.celery.tasks.video_summary_tasks import (
    download_and_generate_video_summmary_task, generate_video_summary_task)
from api.db.database import get_db
from api.utils.files import upload_files
from api.utils.logger import logging
from api.utils.success_response import success_response
from api.v1.schemas.ai_tools.youtube import YTLinksRequest
from api.v1.services.job import job_service
from api.v1.schemas.project import ProjectToolsEnum


video_summary = APIRouter(prefix="/tools/summary", tags=["Tools"])

FILE_DIRECTORY = "summary_files"


@video_summary.post(
    "/video_batch",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=success_response
)
async def enqueue_summarize_batch_job(
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
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

    job_ids = []

    for file in uploaded_files:
        job = generate_video_summary_task.delay(file)

        project = job_service.create_project_with_job(
            job=job, project_title="New project",
            project_type=ProjectToolsEnum.youtube_summarizer.value
        )

        job_ids.append({
            "job_id": job.id,
            "project_id": project.id,
        })
    return success_response(
        status_code=status.HTTP_202_ACCEPTED,
        message="Video summary generation task initiated successfully",
        data={
            "job_ids": job_ids
        }
    )


@video_summary.post(
    "/youtube_batch",
    status_code=status.HTTP_200_OK,
    response_model=success_response,
)
async def summarize_yt_vid(
    request: YTLinksRequest,
    db: Session = Depends(get_db)
):
    """Endpoint to download and summarize a single youtube video"""

    data = []
    for link in request.links:
        task = download_and_generate_video_summmary_task.delay(link)
        logging.info(f"Background task started {task.id}")

        project = job_service.create_project_with_job(
            job=task,
            project_title="New project",
            project_type=ProjectToolsEnum.youtube_summarizer.value
        )
        data.append({
            "job_id": task.id,
            "project_id": project.id,
        })

    return success_response(
        status_code=202,
        message="Summary generation job initiated successfully",
        data={
            "job_ids": data,
        },
    )
