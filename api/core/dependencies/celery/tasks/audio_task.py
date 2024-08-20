import json
from api.core.dependencies.celery.celery_app import worker
from api.v1.services.ai_tools.audio_transcriber import  translate_text
from api.db.database import get_db

db = next(get_db())


@worker.task()
def translate_text_task(text: str, target_language: str):
    """Celery task for translating text."""
    
    translation =  translate_text(text, target_language)
    return translation
