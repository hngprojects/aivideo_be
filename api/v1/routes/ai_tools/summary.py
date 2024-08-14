from fastapi import (
    BackgroundTasks,
    Depends,
    status,
    APIRouter,
    HTTPException,
    File,
    UploadFile,
)
from sqlalchemy.orm import Session
from pypdf import PdfReader
from datetime import timedelta
import os

from api.db.database import get_db
from api.utils.success_response import success_response
from api.utils.files import upload_file
from api.v1.schemas.project import CreateProject
from api.utils.language_code import LANGUAGE_CODES
from api.core.dependencies.translator_service import translate_text
from api.v1.schemas.translation import TranslationRequest
from api.v1.models.project import Project
from api.v1.services.project import project_service
from api.v1.services.ai_tools.summary import summary_service
from api.v1.services.job import job_service
from api.core.dependencies.celery.tasks.summary_tasks import generate_pdf_summary_task

summary = APIRouter(prefix="/tools/summary", tags=["Tools"])


@summary.post(
    "/pdf-summarizer",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=success_response,
)
async def summarize_pdf(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Endpoint to summarize PDF"""

    pdf_file_path = await upload_file(
        file, allowed_extensions=["pdf"], upload_folder="pdf", save_extension="pdf"
    )

    try:
        # Run task in the background
        task = generate_pdf_summary_task.delay(pdf_file_path)

        # Create project with job
        project = job_service.create_project_with_job(
            job=task,
            project_title="New project",
            project_type="PDF Summarizer",
        )

        return success_response(
            status_code=202,
            message="Summary generation job initiated successfully",
            data={
                "job_id": task.id,
                "project_id": project.id,
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@summary.post('/translate-summary', status_code=status.HTTP_200_OK, response_model=success_response)
async def translate_summary(translation_request: TranslationRequest):
    """Endpoint to translate summary into different languages"""
    target_language = translation_request.target_language.lower().replace(" ", "_")

    if target_language not in LANGUAGE_CODES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported language. Supported languages are: {', '.join(LANGUAGE_CODES.keys())}"
        )

    try:
        translated_text = translate_text(translation_request.summary, LANGUAGE_CODES[target_language])

        return success_response(
            status_code=200,
            message="Translation successful",
            data={
                "original_summary": translation_request.summary,
                "translated_summary": translated_text,
                "target_language": target_language
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred during translation: {str(e)}"
        )

