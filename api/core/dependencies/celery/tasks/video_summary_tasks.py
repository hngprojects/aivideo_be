#!/usr/bin/env python3
"""Tasks that handle video transcription and summarization"""
from api.utils.files import convert_video_to_audio, delete_file
from api.v1.services.ai_tools.youtube_summarizer import transcription_service
from api.core.dependencies.celery.celery_app import worker
from api.db.database import get_db
import json
from api.utils.ytdownload import download_video

db = next(get_db())


@worker.task()
def generate_video_summary_task(video_file):
    """Background task to summarize a video and save to database"""

    try:
        audio_file_path = convert_video_to_audio(video_file)

        transcription = transcription_service.transcribe_audio(audio_file_path)
        return json.dumps(transcription)
    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        delete_file(video_file)
        # Re-raise the exception after handling cleanup
        if "e" in locals():
            raise e


@worker.task()
def download_and_generate_video_summmary_task(link):
    """Background task to download youtube video and summarize it and save to db"""
    video_file = download_video(link)
    try:
        audio_file_path = convert_video_to_audio(video_file)

        transcription = transcription_service.transcribe_audio(audio_file_path)
        return json.dumps(transcription)
    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        delete_file(video_file)
        # Re-raise the exception after handling cleanup
        if "e" in locals():
            raise e
