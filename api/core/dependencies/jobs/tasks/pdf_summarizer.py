import json, sys
from uuid import uuid4
from pypdf import PdfReader
import os
import secrets
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from io import BytesIO
from api.utils.files import delete_file
from api.utils.minio_service import minio_service
from api.utils.settings import settings
from api.utils.mime_types import APPLICATION_PDF
from api.v1.services.ai_tools.summary import summary_service


payload = json.loads(sys.argv[1])

pdf_file_url = payload.get('pdf_file_url')

print(f'Downloading and opening PDF file from {pdf_file_url}...')
pdf_file_path = minio_service.download_file_from_minio(pdf_file_url)

try:
    print('Summarizing PDF...')
    # Summarize the PDF
    summary = summary_service.summarize_pdf(pdf_file_path)

    # Process the PDF to extract page and text information
    pdf_reader = PdfReader(pdf_file_path)
    print('Getting number of pages...')
    number_of_pages = len(pdf_reader.pages)
    extracted_text = ""

    for page in pdf_reader.pages:
        extracted_text += page.extract_text() or ""

    print('Getting number of workds and edtimated read time...')
    number_of_words = len(extracted_text.split())
    estimated_read_time = (number_of_words / 250)  # Assuming 250 words per minute reading speed

    print('Calculating time saved in reading summary...')
    summary_word_count = len(summary.split())
    summary_read_time = summary_word_count / 250

    time_saved = estimated_read_time - summary_read_time

    # Create the PDF with better formatting
    print('Setting up storage location for generated summary PDF...')
    pdf_buffer = BytesIO()
    pdf_filename = os.path.join(settings.TEMP_DIR, f"summary-{secrets.token_hex(8)}.pdf")
    os.makedirs(os.path.dirname(pdf_filename), exist_ok=True)

    # Set up the document
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Title
    title_style = styles["Title"]
    story.append(Paragraph("Summary Report", title_style))
    story.append(Spacer(1, 12))

    normal_style = styles["Normal"]
    paragraphs = summary.split("\n\n")

    for paragraph in paragraphs:
        story.append(Paragraph(paragraph, normal_style))
        story.append(Spacer(1, 12))

    doc.build(story)

    # Save the PDF content to a file
    print('Saving PDF to file...')
    pdf_buffer.seek(0)
    with open(pdf_filename, "wb") as f:
        f.write(pdf_buffer.read())

    pdf_buffer.close()

    print('Getting preview and download URL for generated summary PDF...')
    # Upload file to minio server
    bucket_name = "pdf-summarizer"
    preview_url, download_url = minio_service.upload_to_minio(
        bucket_name=bucket_name,
        source_file=pdf_filename,
        destination_file=f"pdfsum-{str(uuid4())}.pdf",
        content_type=APPLICATION_PDF,
    )
    
    print('Cleaning up...')
    delete_file(pdf_filename)

    # Remove binary data from the result dictionary
    result = {
        "number_of_pages": number_of_pages,
        "number_of_words": number_of_words,
        "estimated_read_time": f"{estimated_read_time:.2f} minutes",
        "summary_word_count": summary_word_count,
        "summary_read_time": f"{summary_read_time:.2f} minutes",
        "time_saved": f"{time_saved:.2f} minutes",
        "summary": summary,
        "preview_url": preview_url,
        "download_url": download_url,
    }
    print('Done!!!')

    result_json = json.dumps(result, default=str)
    print(result_json)

except Exception as e:
    # Ensure that files are deleted even if an exception occurs
    if os.path.exists(pdf_filename):
        os.remove(pdf_filename)
    if os.path.exists(pdf_file_path):
        os.remove(pdf_file_path)
    raise Exception(f"Summarization failed: {str(e)}")