#!/usr/bin/env python3
"""Tasks that handle video transcription and summarization"""
from api.utils.files import convert_video_to_audio, delete_file
from api.v1.services.ai_tools.youtube_summarizer import transcription_service
from api.core.dependencies.celery.celery_app import worker
from api.db.database import get_db
import json
from api.utils.ytdownload import download_video
from api.v1.services.ai_tools.summary import summary_service

db = next(get_db())


@worker.task()
def generate_video_summary_task(video_file):
    """Background task to summarize a video and save to database"""

    try:
        transcription = summary_service.summarize_audio(video_file)
        return json.dumps(transcription)
    except Exception as e:
        raise e
    finally:
        try:
            delete_file(video_file)
        except Exception as deletion_error:
            print(str(deletion_error))
        # Re-raise the exception after handling cleanup


@worker.task()
def download_and_generate_video_summmary_task(link):
    """Background task to download youtube video and summarize it and save to db"""
    video_file = download_video(link)
    try:
        transcription = summary_service.summarize_audio(video_file)
        return json.dumps(transcription)
    except Exception as e:
        raise e
    finally:
        try:
            delete_file(video_file)
        except Exception as deletion_error:
            print(str(deletion_error))
        # Re-raise the exception after handling cleanup


def delete_pdf(path):
    try:
        delete_file(path)
    except Exception as deletion_error:
        print(str(deletion_error))
    # Re-raise the exception after handling cleanup
