from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from api.core.dependencies.celery.tasks.video_summary_tasks import (
    download_and_generate_video_summmary_task,
    generate_video_summary_task,
    delete_pdf,
)
from api.db.database import get_db
from api.utils.files import upload_files
from api.utils.logger import logging
from api.utils.pdf_transform import pdf_transform
from api.utils.success_response import success_response
from api.v1.schemas.ai_tools.youtube import PdfDownloadRequest, VideoLinkRequest

from api.v1.services.job import job_service

yt_summary = APIRouter(prefix="/tools/summary", tags=["Tools"])
download = APIRouter(prefix="/tools/download", tags=["Download"])


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


@download.post("/pdf", status_code=status.HTTP_202_ACCEPTED)
def download_pdf(request: PdfDownloadRequest):
    try:
        # Generate PDF
        pdf_path = pdf_transform(
            request.transcript, request.summary, request.video_title
        )
        task = delete_pdf.delay(pdf_path)
        project = job_service.create_project_with_job(
            job=task, project_title="New project", project_type="YT video Summarizer"
        )
        # Return the PDF file
        return FileResponse(
            str(pdf_path),
            media_type="application/pdf",
            filename="transcript_summary.pdf",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
