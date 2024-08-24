import json
from pypdf import PdfReader
import os
import secrets 
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ListStyle
from reportlab.platypus import ListFlowable, ListItem
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from io import BytesIO
from reportlab.lib.enums import TA_CENTER
from io import BytesIO
from api.core.dependencies.celery.celery_app import worker
from api.utils.files import delete_file
from api.v1.services.ai_tools.summary import summary_service
from api.v1.services.ai_tools.yt_summary import yts_service
from api.db.database import get_db
from api.v1.services.ai_tools.audio_transcriber import transcribe_audio_file_with_timestamps

db = next(get_db())


@worker.task()
def generate_pdf_summary_task(pdf_file_path):
    """Background task to summarize a pdf and save to the database"""
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
        estimated_read_time = (
            number_of_words / 250
        )  # Assuming 250 words per minute reading speed

        summary_word_count = len(summary.split())
        summary_read_time = summary_word_count / 250

        time_saved = estimated_read_time - summary_read_time

        # Create the PDF with better formatting
        pdf_buffer = BytesIO()
        pdf_filename = os.path.join("media/uploads/pdf", f"summary_{secrets.token_hex(8)}.pdf")
        os.makedirs(os.path.dirname(pdf_filename), exist_ok=True)

        # Set up the document
        doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        # Title
        title_style = styles['Title']
        story.append(Paragraph("Summary Report", title_style))
        story.append(Spacer(1, 12))

        
        normal_style = styles['Normal']
        paragraphs = summary.split("\n\n") 

    
        for paragraph in paragraphs:
            story.append(Paragraph(paragraph, normal_style))
            story.append(Spacer(1, 12))
    
        doc.build(story)

        # Save the PDF content to a file
        pdf_buffer.seek(0)
        with open(pdf_filename, "wb") as f:
            f.write(pdf_buffer.read())

        pdf_buffer.close()

        # Remove binary data from the result dictionary
        result = {
            "number_of_pages": number_of_pages,
            "number_of_words": number_of_words,
            "estimated_read_time": f"{estimated_read_time:.2f} minutes",
            "summary_word_count": summary_word_count,
            "summary_read_time": f"{summary_read_time:.2f} minutes",
            "time_saved": f"{time_saved:.2f} minutes",
            "summary": summary,
            "pdf_file_path": pdf_filename
        }

        result_json = json.dumps(result, default=str)
        return result_json

    except Exception as e:
        raise Exception(f"Summarization failed: {str(e)}")


@worker.task()
def generate_yt_transcript(video_pth):
    """background task generates a transcript based off yt video"""

    summary = yts_service.summarize_video(video_pth)
    return json.dumps(summary)

@worker.task()
def generate_podcast_summary_task(audio_file):
    '''BAckground task to summarize a podcast and save to database'''

    summary, transcription = summary_service.summarize_podcast(audio_file)
    return json.dumps({
        'summary': summary,
        'transcript': transcription
    })

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