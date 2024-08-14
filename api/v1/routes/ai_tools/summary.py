# from datetime import timedelta
from fastapi import (
    BackgroundTasks,
    Depends,
    status,
    APIRouter,
    Response,
    Request,
    File,
    UploadFile,
    HTTPException,
)
from pypdf import PdfReader
from sqlalchemy.orm import Session



from api.db.database import get_db
from api.utils.success_response import success_response
from api.utils.files import upload_file
from api.v1.schemas.project import CreateProject
from api.utils.language_code import LANGUAGE_CODES
from api.core.dependencies.translator_service import translate_text
from api.v1.schemas.translation import TranslationRequest
from api.v1.services.project import project_service
from api.v1.services.celery import celery_service
from api.v1.services.ai_tools.summary import summary_service
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
        final_summary = summary_service.summarize_pdf(pdf_file_path)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    pdf_reader = PdfReader(pdf_file_path)
    number_of_pages = len(pdf_reader.pages)
    extracted_text = ""
    for page in pdf_reader.pages:
        extracted_text += page.extract_text() or ""

    number_of_words = len(extracted_text.split())
    estimated_read_time = number_of_words / 250

    summary_word_count = len(final_summary.split())
    summary_read_time = summary_word_count / 250

    time_saved = estimated_read_time - summary_read_time

    file_name = file.filename

    # Run task in the background
    task = generate_pdf_summary_task.delay(pdf_file_path)

    # Create a new project entry associated with the Celery task
    project_schema = CreateProject(
        title="PDF Summary Project",
        project_type="PDF Summarizer",
    )
    project = project_service.create(db=db, schema=project_schema)

    # Create a Celery task entry in the database
    celery_service.create_task(task_id=task.id, project_id=project.id)

    return success_response(
        status_code=202,
        message="Summary generation task initiated successfully",
        data={
            "file_name": file_name,
            "number_of_pages": number_of_pages,
            "estimated_read_time": f"{estimated_read_time:.2f} minutes",
            "summary_word_count": summary_word_count,
            "summary_read_time": f"{summary_read_time:.2f} minutes",
            "time_saved": f"{time_saved:.2f} minutes",
            "summary": final_summary,
            "task_id": task.id,
        },
    )   


@summary.post('/translate-summary', status_code=status.HTTP_200_OK, response_model=success_response)
async def translate_summary(translation_request: TranslationRequest):
    '''Endpoint to translate summary into different languages'''
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