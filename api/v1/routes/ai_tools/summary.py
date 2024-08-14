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

# Set a maximum file size (e.g., 10 MB)
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


@summary.post(
    "/pdf-summarizer",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=success_response,
)
async def summarize_pdf(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Endpoint to summarize PDF"""

    # Read the file content to determine its size
    contents = await file.read()
    file_size = len(contents)

    # Rewind the file pointer to the beginning
    await file.seek(0)

    # Check if the uploaded file exceeds the maximum file size
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413, detail="File size exceeds the maximum limit of 10 MB"
        )

    # Check if the uploaded file is empty
    if file_size == 0:
        raise HTTPException(status_code=400, detail="The uploaded PDF file is empty")

    pdf_file_path = await upload_file(
        file, allowed_extensions=["pdf"], upload_folder="pdf", save_extension="pdf"
    )
    # Run task
    task = generate_pdf_summary_task.delay(pdf_file_path)

    # Create project with job
    project = job_service.create_project_with_job(
        job=task,
        project_title="New project",
        project_type="PDF Summarizer",
        # user_id = pass in the current user id for authenticated users
    )

    return success_response(
        status_code=202,
        message="Summary generation job initiated successfully",
        data={
            "job_id": task.id,
            "project_id": project.id,
            "file_name": file.filename,
        },
    )


@summary.post(
    "/translate-summary",
    status_code=status.HTTP_200_OK,
    response_model=success_response,
)
async def translate_summary(translation_request: TranslationRequest):
    """Endpoint to translate summary into different languages"""
    target_language = translation_request.target_language.lower().replace(" ", "_")

    if target_language not in LANGUAGE_CODES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported language. Supported languages are: {', '.join(LANGUAGE_CODES.keys())}",
        )

    try:
        translated_text = translate_text(
            translation_request.summary, LANGUAGE_CODES[target_language]
        )

        return success_response(
            status_code=200,
            message="Translation successful",
            data={
                "original_summary": translation_request.summary,
                "translated_summary": translated_text,
                "target_language": target_language,
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An error occurred during translation: {str(e)}"
        )
