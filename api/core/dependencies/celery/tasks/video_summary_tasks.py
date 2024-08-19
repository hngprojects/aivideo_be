"""Tasks that handle video transcription and summarization"""
from api.utils.files import delete_file
from api.core.dependencies.celery.celery_app import worker
import json
from api.v1.services.ai_tools.yt_summary import yts_service
from api.v1.services.ai_tools.summary import summary_service


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
    video_file = yts_service.download_video(link)
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
def delete_pdf(path):
    try:
        delete_file(path)
    except Exception as deletion_error:
        print(str(deletion_error))
    # Re-raise the exception after handling cleanup
