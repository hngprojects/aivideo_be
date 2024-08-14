import json
from celery import shared_task

from api.core.dependencies.celery.celery_app import worker
from api.v1.services.ai_tools.summary import summary_service
from api.v1.services.ai_tools.yt_summary import yts_service
from api.db.database import get_db

db = next(get_db())


@worker.task()
def generate_pdf_summary_task(pdf_file):
    """BAckground task to summarize a pdf and save to database"""

    summary = summary_service.summarize_pdf(pdf_file)

    return summary

@worker.task()
def generate_yt_transcript(video_pth):
    """background task generates a transcript based off yt video"""

    summary = yts_service.summarize_video(video_pth)
    return summary
