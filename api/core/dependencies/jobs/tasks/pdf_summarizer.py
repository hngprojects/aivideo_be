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
from api.utils.settings import settings
from api.utils import mime_types
from api.v1.services.ai_tools.summary import summary_service, pdf_summary_service
from api.db.database import get_db
from api.utils.minio_service import minio_service
from api.v1.services.job import tifi_job_service
from api.core.dependencies.jobs.utils import save_and_print_job_progress

db = next(get_db())

payload = json.loads(sys.argv[1])

job_id = payload.get('job_id', None)
job = tifi_job_service.fetch(db, job_id)

save_and_print_job_progress(db, job, 0, 'Job started')

pdf_file_url = payload.get('pdf_file_url')

save_and_print_job_progress(db, job, 10, f'Downloading and opening PDF file from {pdf_file_url}')
pdf_file_path = minio_service.download_file_from_minio(pdf_file_url)
    
# Extract text from the PDF
save_and_print_job_progress(db, job, 30, 'Extracting data from uploaded PDF')
pdf_data = pdf_summary_service.extract_pdf_data(pdf_file_path)

# Split the text into chunks
save_and_print_job_progress(db, job, 40, 'Breaking PDF text into chunks for processing')
chunks = pdf_summary_service.split_text_into_chunks(pdf_data.get('text'))

# Summarize each chunk
save_and_print_job_progress(db, job, 50, 'Generating summary for PDF chunks')
summaries = []
for chunk in chunks:
    summary = pdf_summary_service.summarize_text(chunk)
    summaries.append(summary)

# Combine the summaries
save_and_print_job_progress(db, job, 60, 'Generating final summary for PDF')
final_summary = "\n".join(summaries)

save_and_print_job_progress(db, job, 70, 'Making calculations')
# Calculate time saved
time_saved = pdf_summary_service.get_reading_time(pdf_data.get('text'))- pdf_summary_service.get_reading_time(final_summary)
# Calculate summary word count
summary_word_count = len(final_summary.split())

# Save summary to PDF
save_and_print_job_progress(db, job, 75, 'Saving summary to pdf')
summary_pdf_file = pdf_summary_service.save_summary_to_pdf(text=final_summary)

save_and_print_job_progress(db, job, 85, 'Generating summary PDF preview and download link')
preview_url, download_url = minio_service.upload_to_minio(
    bucket_name='pdf-summarizer',
    source_file=summary_pdf_file,
    destination_file=f"pdfsum-{str(uuid4())}.pdf",
    content_type=mime_types.APPLICATION_PDF,
)

save_and_print_job_progress(db, job, 90, 'Generating result and performing final cleanup')

# Remove text data from the pdf_data dictionary
pdf_data.pop('text')
delete_file(pdf_file_path)

result = json.dumps({
    **pdf_data,
    'summary': final_summary,
    'summary_word_count': summary_word_count,
    'summary_read_time': f'{pdf_summary_service.get_reading_time(final_summary)} minutes',
    'time_saved': f'{time_saved} minutes',
    "preview_url": preview_url,
    "download_url": download_url,
})
save_and_print_job_progress(db, job, 95)

print(result)
