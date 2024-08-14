from celery import shared_task

from api.core.dependencies.celery.celery_app import worker
from api.v1.services.ai_tools.summary import summary_service
from api.db.database import get_db

db = next(get_db())

@worker.task()
def generate_pdf_summary_task(pdf_file):
    '''BAckground task to summarize a pdf and save to database'''

    summary = summary_service.summarize_pdf(pdf_file)
    return summary


@worker.task()
def generate_audio_summary_task(audio_file, target_lang):
    '''Background task to summarize an audio file and save to the database'''

    """Process the audio file: transcribe, summarize, translate, and export"""
    result = summary_service.process_audio(audio_file, target_lang)
    return result