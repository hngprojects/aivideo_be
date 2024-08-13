from api.core.dependencies.celery.celery_app import worker
from api.v1.services.ai_tools.summary import summary_service
from api.db.database import get_db

db = next(get_db())


@worker.task()
def generate_pdf_summary_task(pdf_file_path):
    '''BAckground task to summarize a pdf and save to database'''
    try:
        summary = summary_service.summarize_pdf(pdf_file_path)

        return summary
    
    except Exception as e:
        raise Exception(f"Summarization failed: {str(e)}")
