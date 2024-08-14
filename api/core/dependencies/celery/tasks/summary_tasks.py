from celery import shared_task
from pypdf import PdfReader
import json
from api.core.dependencies.celery.celery_app import worker
from api.v1.services.ai_tools.summary import summary_service
from api.db.database import get_db

db = next(get_db())

@worker.task()
def generate_pdf_summary_task(pdf_file_path):
    '''Background task to summarize a pdf and save to database'''
    try:
        # Summarize the PDF
        summary = summary_service.summarize_pdf(pdf_file_path)
        
        # Process the PDF to extract page and text information
        pdf_reader = PdfReader(pdf_file_path)
        number_of_pages = len(pdf_reader.pages)
        extracted_text = ""
        for page in pdf_reader.pages:
            extracted_text += page.extract_text() or ""

        number_of_words = len(extracted_text.split())
        estimated_read_time = number_of_words / 250

        summary_word_count = len(summary.split())
        summary_read_time = summary_word_count / 250

        time_saved = estimated_read_time - summary_read_time

        # Create the result dictionary
        result = {
            
            "number_of_pages": number_of_pages,
            "number_of_words": number_of_words,
            "estimated_read_time": f"{estimated_read_time:.2f} minutes",
            "summary_word_count": summary_word_count,
            "summary_read_time": f"{summary_read_time:.2f} minutes",
            "time_saved": f"{time_saved:.2f} minutes",
            "summary": summary
        }

        return json.dumps(result)
    
    except Exception as e:
        raise Exception(f"Summarization failed: {str(e)}")
