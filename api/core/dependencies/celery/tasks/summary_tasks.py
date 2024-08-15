import json
from celery import shared_task

from api.core.dependencies.celery.celery_app import worker
from api.utils.files import delete_file
from api.v1.services.ai_tools.summary import summary_service
from api.db.database import get_db

db = next(get_db())

@worker.task()
def generate_pdf_summary_task(pdf_file):
    '''BAckground task to summarize a pdf and save to database'''

    summary = summary_service.summarize_pdf(pdf_file)

    # Delete file from file system
    delete_file(pdf_file)

    return summary
