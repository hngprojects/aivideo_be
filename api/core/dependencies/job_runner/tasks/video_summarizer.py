"""Tasks that handle video transcription and summarization"""
from api.utils.files import delete_file
import json, sys
from api.utils.transcripts import create_documents_from_transcript, get_paragraphs
from api.v1.services.ai_tools.video_subtitles import convert_video_to_audio, transcribe_audio_segments
from api.v1.services.ai_tools.summary import summary_service
from api.db.database import get_db
from api.utils.minio_service import minio_service
from api.v1.services.job import tifi_job_service
from api.core.dependencies.job_runner.app.utils import save_and_print_job_progress

db = next(get_db())

payload = json.loads(sys.argv[1])

job_id = payload.get('job_id', None)
job = tifi_job_service.fetch(db, job_id)

save_and_print_job_progress(db, job, 0, 'Job started')

audio_file = None
video_url = payload.get('video_url')

save_and_print_job_progress(db, job, 10, f'Downloading and opening video file from {video_url}')
video_file = minio_service.download_file_from_minio(video_url)

save_and_print_job_progress(db, job, 30, 'Extracting audio from video')
audio_file = convert_video_to_audio(video_file)

save_and_print_job_progress(db, job, 50, 'Transcribing audio')
transcription = transcribe_audio_segments(audio_file)

save_and_print_job_progress(db, job, 70, 'Generating transcript documents for summarization')
documents, transcript = create_documents_from_transcript(transcription)

save_and_print_job_progress(db, job, 80, 'Summarizing transcript')
summary = summary_service.summarize_transcript(documents)

save_and_print_job_progress(db, job, 85, 'Cleaning up')
delete_file(video_file)
if audio_file:
    delete_file(audio_file)

save_and_print_job_progress(db, job, 90, 'Generating result data')
result = {
    "summary": summary,
    "summary_word_count": summary_service.calculate_word_count(summary),
    "transcript": get_paragraphs(transcription),
    "transcript_word_count": summary_service.calculate_word_count(transcript)
}

save_and_print_job_progress(db, job, 95)

print(json.dumps(result))
