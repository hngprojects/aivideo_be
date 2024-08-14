# audio_transcriber.py
from fastapi import FastAPI, UploadFile, File, HTTPException, APIRouter
from api.v1.schemas.audio_transcriber import TranslationRequest
from api.core.dependencies.celery.tasks.summary_tasks import  transcribe_audio_task, translate_text_task
from api.v1.services.job import job_service

AUDIOFILE = "audio.mp3"  
audio = APIRouter(prefix="/tools/audio-transcribe", tags=["Tools"])

@audio.post("/upload/")
async def upload_audio(file: UploadFile = File(...)):
    """Upload and transcribe audio file."""
    try:
        file_path = AUDIOFILE
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())

        task = transcribe_audio_task.delay(file_path)
        
        project = job_service.create_project_with_job(
            job=task,
            project_title='New Audio Transcription Project',
            project_type='Audio Transcription'
        )

        return {
            "status_code": 200,
            "message": "Audio transcription job initiated successfully",
            "data": {
                "job_id": task.id,
                "project_id": project.id,
            }
        }
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

        return {
            "status_code": 200,
            "message": "Text translation job initiated successfully",
            "data": {
                "job_id": task.id,
                "project_id": project.id,
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
