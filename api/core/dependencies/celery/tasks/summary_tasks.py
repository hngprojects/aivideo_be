import json
from celery import shared_task

from api.core.dependencies.celery.celery_app import worker
from api.v1.services.ai_tools.summary import summary_service
from api.v1.services.ai_tools.audio_transcriber import transcribe_audio, translate_text

from api.db.database import get_db

db = next(get_db())

@worker.task()
def generate_pdf_summary_task(pdf_file):
    '''BAckground task to summarize a pdf and save to database'''

    summary = summary_service.summarize_pdf(pdf_file)
    return summary

@worker.task()
def transcribe_audio_task(file_path: str):
    """Celery task for transcribing audio."""
    return transcribe_audio(file_path)

@worker.task()
def translate_text_task(text: str, target_language: str):
    """Celery task for translating text."""
    return translate_text(text, target_language)