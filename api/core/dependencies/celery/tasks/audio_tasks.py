import json
from celery import shared_task
from api.core.dependencies.celery.celery_app import worker
from api.v1.services.ai_tools.summary_audio import summary_service
from api.db.database import get_db
import base64
from typing import Dict
import json
from api.v1.services.ai_tools.audio_transcriber import transcribe_audio_file_with_timestamps

# Initialize the database session
db = next(get_db())

@worker.task()
def generate_audio_summary_task(audio_file, target_lang):
    '''Background task to summarize an audio file and save to the database'''

    # Process the audio file: transcribe, summarize, translate, and export
    result = summary_service.process_audio(audio_file, target_lang)
    return json.dumps(result)

    
@worker.task()
def transcribe_audio_task(audio_data):
    result = transcribe_audio_file_with_timestamps(audio_data)
    return json.dumps(result)