import json, sys
from uuid import uuid4
from api.utils.files import delete_file
from api.utils import mime_types
from api.v1.services.ai_tools.pdf_summarizer import pdf_summary_service
from api.db.database import get_db
from api.utils.minio_service import minio_service
from api.v1.services.job import tifi_job_service
from api.core.dependencies.job_runner.app.utils import save_and_print_job_progress

db = next(get_db())

payload = json.loads(sys.argv[1])

job_id = payload.get('job_id', None)
job = tifi_job_service.fetch(db, job_id)

save_and_print_job_progress(db, job, 0, 'Job started')

pdf_file_url = payload.get('pdf_file_url')
detail_level = payload.get('detail_level')

save_and_print_job_progress(db, job, 10, f'Downloading and opening PDF file from {pdf_file_url}')
pdf_file_path = minio_service.download_file_from_minio(pdf_file_url)

try:
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
        summary = pdf_summary_service.summarize_text(chunk, detail_level=detail_level)
        summaries.append(summary)

    # Combine the summaries
    save_and_print_job_progress(db, job, 60, 'Generating final summary for PDF')
    final_summary = "\n".join(summaries)

    save_and_print_job_progress(db, job, 70, 'Making calculations')
    # Calculate time saved
    time_saved = pdf_summary_service.get_reading_time(pdf_data.get('text'))- pdf_summary_service.get_reading_time(final_summary)
    # Calculate summary word count
    summary_word_count = len(final_summary.split())
    # Calculate summary read time
    summary_read_time = pdf_summary_service.get_reading_time(summary)
    estimated_summary_read_time = f'{summary_read_time} minute' if summary_read_time == 1 else f'{summary_read_time} minutes'

    # Save summary to PDF
    save_and_print_job_progress(db, job, 75, 'Saving summary to pdf')
    summary_pdf_file = pdf_summary_service.save_summary_to_pdf(text=final_summary)

    save_and_print_job_progress(db, job, 85, 'Generating summary PDF preview and download link')
    preview_url, download_url = minio_service.upload_to_minio(
        folder_name='pdf-summarizer',
        source_file=summary_pdf_file,
        destination_file=f"pdfsum-{str(uuid4())}.pdf",
        content_type=mime_types.APPLICATION_PDF,
    )

    save_and_print_job_progress(db, job, 90, 'Generating result and performing final cleanup')

    # Remove text data from the pdf_data dictionary
    pdf_data.pop('text')
    delete_file(summary_pdf_file)

    result = json.dumps({
        **pdf_data,
        'summary': final_summary,
        'summary_word_count': summary_word_count,
        'summary_read_time': estimated_summary_read_time,
        'time_saved': f'{time_saved} minute' if time_saved == 1 else f'{time_saved} minutes',
        "preview_url": preview_url,
        "download_url": download_url,
    })
    save_and_print_job_progress(db, job, 95)

    print(result)

except Exception as e:
    raise e
    
finally:
    delete_file(pdf_file_path)
