import base64
import json

from celery.result import AsyncResult
from fastapi import (APIRouter, Depends, File, HTTPException, Request,
                     UploadFile, status)
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from api.core.dependencies.celery.celery_app import worker
from api.core.dependencies.celery.tasks.video_summary_tasks import (
    download_and_generate_video_summmary_task, generate_video_summary_task)
from api.db.database import get_db
from api.utils.files import delete_file, upload_files
from api.utils.logger import logging
from api.utils.success_response import success_response
from api.utils.tool_limiter import track_tool_usage
from api.v1.models.user import User
from api.v1.schemas.ai_tools.youtube import (PdfDownloadRequest,
                                             VideoLinkRequest,
                                             VideoTranslationRequest)
from api.v1.schemas.project import ProjectToolsEnum
from api.v1.services.ai_tools.audio_transcriber import translate_text
from api.v1.services.ai_tools.yt_summary import yts_service
from api.v1.services.job import job_service
from api.v1.services.user import user_service

yt_summary = APIRouter(prefix="/tools/summary", tags=["Tools"])
download = APIRouter(prefix="/tools/download", tags=["Download"])


@yt_summary.post(
    "/video",
    status_code=status.HTTP_200_OK,
    response_model=success_response,
)
@track_tool_usage(ProjectToolsEnum.youtube_summarizer)
async def summarize_up_vid(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(user_service.get_current_user_optional)
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

    task = generate_video_summary_task.delay(video[0])
    logging.info(f"Background task started {task.id}")

    # Create project with job
    project = job_service.create_project_with_job(
        job=task,
        project_title="video upload project",
        project_type=ProjectToolsEnum.youtube_summarizer.value,
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
@track_tool_usage(ProjectToolsEnum.youtube_summarizer)
async def summarize_yt_vid(
    schema: VideoLinkRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(user_service.get_current_user_optional),
):
    """Endpoint to download and summarize a single youtube video"""

    task = download_and_generate_video_summmary_task.delay(schema.link)
    logging.info(f"Background task started {task.id}")

    # Create project with job
    project = job_service.create_project_with_job(
        job=task,
        project_title="Youtube URL Summary",
        project_type=ProjectToolsEnum.youtube_summarizer.value,
        description="New YT Summarizer Project",
    )

    return success_response(
        status_code=202,
        message="Summary generation job initiated successfully",
        data={
            "job_id": task.id,
            "project_id": project.id,
        },
    )


@download.post(
    "/pdf",
    status_code=status.HTTP_200_OK,
    response_model=success_response,
)
def download_pdf(
    request: PdfDownloadRequest,
):
    try:
        # Generate PDF
        pdf_path = yts_service.pdf_transform(request)
        # Read the PDF file content
        with open(str(pdf_path), "rb") as pdf_file:
            pdf_content = pdf_file.read()

        # Encode PDF content to Base64
        encoded_pdf = base64.b64encode(pdf_content).decode("utf-8")

        # Delete the file after encoding
        delete_file(str(pdf_path))
        # Return the PDF file
        return success_response(
            status_code=200,
            message="PDF generated successfully",
            data={"pdf_data": encoded_pdf},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@yt_summary.post(
    "/translate_job_result",
    status_code=status.HTTP_200_OK,
    response_model=success_response
)
def translate_job_id(
    request: VideoTranslationRequest,
):
    """Endpoint to translate the summary and transcript of a video"""
    job = AsyncResult(request.job_id, app=worker)
    translate_result = None

    if job.result is None and job.state != "SUCCESS":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job not completed"
        )
    result = json.loads(str(job.result))

    translate_result = translate_text(result, request.language)

    return success_response(
        status_code=status.HTTP_200_OK,
        message="Translation successful",
        data={
            "result": translate_result
        }
    )
