# audio_transcriber.py
from fastapi import FastAPI, UploadFile, File, HTTPException, APIRouter
from api.v1.schemas.audio_transcriber import TranslationRequest
from api.core.dependencies.celery.tasks.audio_task import   translate_text_task
from api.v1.services.job import job_service
from api.utils.success_response import success_response

 
audio = APIRouter(prefix="/tools/audio-transcribe", tags=["Tools"])



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