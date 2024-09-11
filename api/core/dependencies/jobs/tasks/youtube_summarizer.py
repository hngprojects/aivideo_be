from api.utils.files import delete_file, download_audio_yt
import json, sys
from api.utils.transcripts import create_documents_from_transcript, get_paragraphs
from api.v1.services.ai_tools.video_subtitles import transcribe_audio_segments
from api.v1.services.ai_tools.summary import summary_service
from api.db.database import get_db
from api.v1.services.job import tifi_job_service
from api.core.dependencies.jobs.utils import save_and_print_job_progress

db = next(get_db())

payload = json.loads(sys.argv[1])

job_id = payload.get('job_id', None)
job = tifi_job_service.fetch(db, job_id)

save_and_print_job_progress(db, job, 0, 'Job started')

audio_file = None

save_and_print_job_progress(db, job, 20, 'Downloading and extracting audio from youtube video')
audio_file = download_audio_yt(payload.get('link'))

save_and_print_job_progress(db, job, 40, 'Transcribing audio')
transcription = transcribe_audio_segments(audio_file)

save_and_print_job_progress(db, job, 60, 'Generating transcript documents for summarization')
documents, transcript = create_documents_from_transcript(transcription)

save_and_print_job_progress(db, job, 80, 'Summarizing transcript')
summary = summary_service.summarize_transcript(documents)

if audio_file:
    save_and_print_job_progress(db, job, 85, 'Cleaning up')
    delete_file(audio_file)

save_and_print_job_progress(db, job, 90, 'Generating result')
result = {
    "summary": summary,
    "summary_word_count": summary_service.calculate_word_count(summary),
    "transcript": get_paragraphs(transcription),
    "transcript_word_count": summary_service.calculate_word_count(transcript)
}

save_and_print_job_progress(db, job, 95)

print(json.dumps(result))
