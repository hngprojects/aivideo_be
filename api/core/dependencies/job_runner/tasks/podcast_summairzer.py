import json, sys
import os

from uuid import uuid4
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from io import BytesIO

from api.utils.settings import settings
from api.utils.files import delete_file
from api.v1.services.ai_tools.summary import summary_service
from api.utils import mime_types
from api.db.database import get_db
from api.utils.minio_service import minio_service
from api.v1.services.job import tifi_job_service
from api.core.dependencies.job_runner.app.utils import save_and_print_job_progress

db = next(get_db())

payload = json.loads(sys.argv[1])

job_id = payload.get('job_id', None)
job = tifi_job_service.fetch(db, job_id)

save_and_print_job_progress(db, job, 10)

audio_url = payload.get('audio_url')

audio_file = minio_service.download_file_from_minio(audio_url)

summary, transcription, transcribed_text = summary_service.summarize_podcast(audio_file)
number_of_words = len(transcribed_text.split())
estimated_read_time = (number_of_words / 250)  # Assuming 250 words per minute reading speed

# Create the PDF with better formatting
pdf_buffer = BytesIO()
pdf_filename = os.path.join(settings.TEMP_DIR, f"summary-{str(uuid4())}.pdf")
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

story.append(Paragraph("Transcript", title_style))
story.append(Spacer(1, 12))

normal_style = styles["Normal"]
paragraphs = transcribed_text.split("\n\n")

for paragraph in paragraphs:
    story.append(Paragraph(paragraph, normal_style))
    story.append(Spacer(1, 12))

doc.build(story)

# Save the PDF content to a file
pdf_buffer.seek(0)
with open(pdf_filename, "wb") as f:
    f.write(pdf_buffer.read())

pdf_buffer.close()
minio_save_file = f"podsum-{str(uuid4())}.pdf"
save_url, download_url = minio_service.upload_to_minio(
    bucket_name="podcast-summary",
    source_file=pdf_filename,
    destination_file=minio_save_file,
    content_type=mime_types.APPLICATION_PDF,
)
delete_file(pdf_filename)

result = json.dumps({
    "summary": summary,
    "transcript": transcription,
    "estimated_read_time": f"{estimated_read_time:.2f} minutes",
    "pdf_file_path": save_url,
    "download_url": download_url,
})

print(result)
