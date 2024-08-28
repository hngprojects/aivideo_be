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
from typing import Optional
import requests
import io
import os
import json
from fastapi.responses import FileResponse

from api.db.database import get_db
from api.utils.success_response import success_response
from api.utils.files import upload_file_to_current_dir
from api.utils.files import upload_file, check_file_size
from api.utils.language_code import LANGUAGE_CODES
from api.v1.schemas.project import ProjectToolsEnum
from api.v1.services.ai_tools.translator_service import translate_text
from api.v1.schemas.translation import TranslationRequest
from api.v1.schemas.ai_tools.audio_transcriber import PodcastRequest
from api.v1.services.ai_tools.summary import summary_service
from api.v1.services.job import job_service
from api.core.dependencies.celery.tasks.summary_tasks import generate_pdf_summary_task, generate_podcast_summary_task, generate_audio_summary_task, transcribe_audio_task

summary = APIRouter(prefix="/tools/summary", tags=["Tools"])

MAX_FILE_SIZE = 15 * 1024 * 1024

@summary.post('/pdf-summarizer-test', 
              status_code=status.HTTP_200_OK, 
              response_model=success_response)
async def summarize_pdf(file: UploadFile = File(...), db: Session = Depends(get_db)):
    '''Endpoint to summarize PDF'''
    
    pdf_file = await upload_file_to_current_dir(
        file, 
        allowed_extensions=['pdf'], 
        save_extension='pdf'
    )

    task = generate_pdf_summary_task.delay(pdf_file)

    # Create project with job
    project = job_service.create_project_with_job(
        job=task,
        project_title='New project',
        project_type=ProjectToolsEnum.pdf_summarizer.value,
        # user_id = pass in the current user id for authenticated users
    )

    return success_response(
        status_code=202,
        message="Summary generation job initiated successfully",
        data={
            "job_id": task.id,
            "project_id": project.id,
        },
    )


@summary.post(
    "/pdf-summarizer",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=success_response,
)
async def summarize_pdf(file: UploadFile = File(...), db: Session = Depends(get_db)
):
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

    # Upload the file and get its path
    pdf_file_path = await upload_file(
        file, allowed_extensions=["pdf"], upload_folder="pdf", save_extension="pdf"
    )
    
    # Run task
    task = generate_pdf_summary_task.delay(pdf_file_path)

    # Create project with job
    project = job_service.create_project_with_job(
        job=task,
        project_title='New project',
        project_type=ProjectToolsEnum.pdf_summarizer.value,
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
    

@summary.get("/download-summary/{job_id}", response_model=success_response)
async def download_summary(job_id: str, db: Session = Depends(get_db)):
    """Return the generated summary's download URL from MinIO"""
    task_result = job_service.fetch_by_job_id(job_id)
    if not task_result or not task_result.result:
        job_service.update_job_result(job_id)
        task_result = job_service.fetch_by_job_id(job_id)
        if not task_result or not task_result.result:
            raise HTTPException(status_code=404, detail="Summary not found")
    try:
        task_result_data = json.loads(task_result.result)
        download_url = task_result_data.get('download_url')
        preview_url = task_result_data.get('preview_url')
        if not download_url:
            raise HTTPException(status_code=404, detail="Download URL not found")
        return success_response(
            status_code=200,
            message="Download URL retrieved successfully",
            data={"download_url": download_url, "preview_url": preview_url}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve download URL: {str(e)}")



@summary.post("/summarize-podcast", status_code=status.HTTP_202_ACCEPTED, response_model=success_response)
async def summarize_podcast(request: PodcastRequest):

    audio_url = summary_service.get_audio_url(request.podcast_url)

    audio_response = requests.get(audio_url)
    if audio_response.status_code == 200:
        file_like_object = io.BytesIO(audio_response.content)
        file_like_object.filename = "podcast.mp3"
        file_path = await upload_file_to_current_dir(
            file_like_object, 
            allowed_extensions=['mp3', 'mp4'], 
            save_extension='mp3',
        )
        task = generate_podcast_summary_task.delay(file_path)
   
        # Create project with job
        project = job_service.create_project_with_job(
            job=task,
            project_title='New project',
            project_type=ProjectToolsEnum.podcast_summarizer.value
            # user_id = pass in the current user id for authenticated users
        )

        return success_response(
            status_code=202,
            message="Podcast Summary generation job initiated successfully",
            data={
                "job_id": task.id,
                "project_id": project.id,
            }
        )
    else:
        return success_response(
            status_code=404,
            message="Podcast not found",
            data={}
        )

@summary.post('/audio-summarizer', status_code=status.HTTP_200_OK, response_model=success_response)
async def summarize_audio(
    file: UploadFile = File(...), 
    target_lang: str = "es",  # Default to Spanish
    db: Session = Depends(get_db)
):
    '''Endpoint to summarize an audio file'''
    
    audio_file = await upload_file(
        file, 
        allowed_extensions=['mp3', 'wav'],
        upload_folder='audio', 
        save_extension='mp3' 
    )
    await check_file_size(file)
    
    task_transcribe = transcribe_audio_task.delay(audio_file)
    task = generate_audio_summary_task.delay(audio_file, target_lang)

    project = job_service.create_project_with_job(
        job=task,
        project_title='New Audio Summarization Project',
        project_type=ProjectToolsEnum.audio_summarizer.value
    )

    project_transcribe = job_service.create_project_with_job(
        job=task_transcribe,
        project_title='New Audio transcription Project',
        project_type=ProjectToolsEnum.audio_transcriber.value
    )

    return success_response(
        status_code=202,
        message="Audio summary generation and transcription  job initiated successfully",
        data={
            "job_id": task.id,
            "project_id": project.id,
            "transcription_job_id": task_transcribe.id,
            "transcription_project_id": project_transcribe.id,

        }
    )
