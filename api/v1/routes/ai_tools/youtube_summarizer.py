#!/usr/bin/env python3
"""Endpoints that handle video transcription and summarization"""

from typing import List
from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm.session import Session
from starlette.status import HTTP_202_ACCEPTED
from api.utils.files import upload_files
from api.db.database import get_db
from api.v1.schemas.project import CreateProject
from api.v1.services.project import project_service
from api.v1.services.job import job_service
from api.core.dependencies.celery.tasks.video_summary_tasks import (
    generate_video_summary_task
)

from api.utils.success_response import success_response


video_summary = APIRouter(prefix="/tools/youtube_summarizer", tags=["Tools"])

FILE_DIRECTORY = "summary_files"


@video_summary.post(
    "/summarize_batch",
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
        allowed_extensions=["mp4"],
        upload_folder=FILE_DIRECTORY,
        save_extension="mp4"
    )

    job_ids = []

    for file in uploaded_files:
        job = generate_video_summary_task.delay(file)

        project = job_service.create_project_with_job(
            job=job, project_title="New project",
            project_type="Youtube summarizer"
        )

        job_ids.append({
            "job_id": job.id,
            "project_id": project.id,
        })
    return success_response(
        status_code=HTTP_202_ACCEPTED,
        message="Video summary generation task initiated successfully",
        data={
            "job_ids": job_ids
        }
    )
