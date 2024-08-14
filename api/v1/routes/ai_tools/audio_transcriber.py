from fastapi import FastAPI, UploadFile, File, HTTPException, APIRouter
from api.v1.schemas.audio_transcriber import TranslationRequest
from api.core.dependencies.celery.tasks.summary_tasks import transcribe_audio_task, translate_text_task
from api.v1.services.job import job_service
import mimetypes

AUDIOFILE = "audio.mp3"  
audio = APIRouter(prefix="/tools/audio-transcribe", tags=["Tools"])

def is_audio_file(filename: str, content_type: str) -> bool:
    """Check if the file is an audio file based on the filename and content type."""
    audio_content_types = [
        'audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/ogg', 'audio/aac'
    ]
    _, ext = mimetypes.guess_type(filename)
    return content_type in audio_content_types and (ext == 'mp3' or ext == 'wav')

@audio.post("/upload/")
async def upload_audio(file: UploadFile = File(...)):
    """Upload and transcribe audio file."""
    if not is_audio_file(file.filename, file.content_type):
        raise HTTPException(status_code=400, detail="Invalid file type. Only audio files are allowed.")
    
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
