from celery import shared_task
import json
from api.utils.files import convert_video_to_audio, delete_file
from api.v1.services.ai_tools.video_subtitles import translate_text, generate_subtitles
from api.v1.services.ai_tools.summary_audio import summary_service

from api.core.dependencies.celery.celery_app import worker
from api.db.database import get_db

db = next(get_db())

@worker.task()
def transcribe_video_task(video_url):
    """Background task to transcribe audio from a video"""
    try:
        # Convert video to audio
        audio_file_path = convert_video_to_audio(video_url)

        # Transcribe audio to text
        transcription = summary_service.transcribe_audio(audio_file_path)

        # Delete the audio file after transcription
        delete_file(audio_file_path)

        return json.dumps(transcription)
    except Exception as e:
        print(f"Transcription failed: {str(e)}")
        raise

@worker.task()
def translate_text_task(text, target_language):
    """Background task to translate text"""
    try:
        # Translate text
        translated_text = translate_text(text, target_language)
        return json.dumps({"original_text": text, "translated_text": translated_text})
    except Exception as e:
        print(f"Translation failed: {str(e)}")
        raise

@worker.task()
def generate_subtitles_task(video_url):
    """Background task to generate subtitles from a video"""
    try:
        # Generate subtitles
        result = generate_subtitles(video_url)
        return json.dumps(result)
    except Exception as e:
        print(f"Subtitle generation failed: {str(e)}")
        raise
