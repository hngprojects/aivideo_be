import base64
import json
from typing import Optional

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
from api.utils.minio_service import minio_service
from api.utils.success_response import success_response
from api.utils.tool_limiter import track_tool_usage
from api.v1.models.user import User
from api.v1.schemas.ai_tools.youtube import PdfDownloadRequest
from api.v1.models.project import ProjectToolsEnum
from api.v1.services.ai_tools.audio_transcriber import translate_text
from api.v1.services.ai_tools.yt_summary import yts_service
from api.v1.services.job import job_service
from api.v1.services.job import tifi_job_service
from api.v1.services.user import user_service

yt_summary = APIRouter(prefix="/tools/summary", tags=["Tools"])
download = APIRouter(prefix="/tools/download", tags=["Download"])


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
