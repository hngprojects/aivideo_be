# audio_transcriber.py
from fastapi import FastAPI, UploadFile, File, HTTPException, APIRouter
from api.v1.schemas.audio_transcriber import TranslationRequest
from api.core.dependencies.celery.tasks.audio_task import  transcribe_audio_task, translate_text_task
from api.v1.services.job import job_service
from api.utils.success_response import success_response
import io

AUDIOFILE = "audio.mp3"  
audio = APIRouter(prefix="/tools/audio-transcribe", tags=["Tools"])

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

@audio.post("/upload/")
async def upload_audio(file: UploadFile = File(...)):
    """Upload and transcribe audio file."""
    try:
        file_content = await file.read()
        
        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File is too large")
        
        file_stream = io.BytesIO(file_content)
        
        task = transcribe_audio_task.delay(file_stream.getvalue())
        
        project = job_service.create_project_with_job(
            job=task,
            project_title='New Audio Transcription Project',
            project_type='Audio Transcription'
        )

        return success_response(
            status_code=200,
            message="Audio transcription job initiated successfully",
            data={
                "job_id": task.id,
                "project_id": project.id,
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@audio.post("/translate/")
async def translate_text_endpoint(request: TranslationRequest):
    """Translate text to the specified language."""
    try:
        task = translate_text_task.delay(request.text, request.target_language)

        # Create project with job
        project = job_service.create_project_with_job(
            job=task,
            project_title='New Translation Project',
            project_type='Text Translation'
        )

        return success_response(
            status_code=  200,
            message="Text translation job initiated successfully",
            data= {
                "job_id": task.id,
                "project_id": project.id,
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))