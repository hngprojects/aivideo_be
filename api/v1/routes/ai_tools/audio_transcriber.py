# audio_transcriber.py
from fastapi import HTTPException, APIRouter
import json
from api.v1.schemas.ai_tools.audio_transcriber import TranslationRequest
from api.core.dependencies.celery.tasks.audio_tasks import translate_text_task
from api.v1.services.job import job_service
from api.utils.success_response import success_response


audio = APIRouter(prefix="/tools/audio-transcribe", tags=["Tools"])


@audio.post("/translate/", response_model=success_response)
async def translate_text_endpoint(request: TranslationRequest):
    """Translate text to the specified language."""
    try:
        # If the text is a dictionary, serialize it to a string for the task
        text_to_translate = json.dumps(request.text) if isinstance(
            request.text, dict) else request.text

        task = translate_text_task.delay(
            text_to_translate, request.target_language)

        project = job_service.create_project_with_job(
            job=task,
            project_title='New Translation Project',
            project_type='Text Translation'
        )

        return success_response(
            status_code=200,
            message="Text translation job initiated successfully",
            data={
                "job_id": task.id,
                "project_id": project.id,
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
