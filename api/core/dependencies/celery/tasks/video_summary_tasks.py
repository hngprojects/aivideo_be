"""Tasks that handle video transcription and summarization"""
from api.utils.files import delete_file, download_audio_yt
from api.core.dependencies.celery.celery_app import worker
import json
from api.utils.transcripts import create_documents_from_transcript, get_paragraphs
from api.v1.services.ai_tools.video_subtitles import convert_video_to_audio, transcribe_audio, transcribe_audio_segments
from api.v1.services.ai_tools.yt_summary import yts_service
from api.v1.services.ai_tools.summary import summary_service


@worker.task(bind=True)
def generate_video_summary_task(self, video_file):
    """Background task to summarize a video and save to database"""

    audio_file = None
    try:
        self.update_state(state='PROGRESS', meta={
            'status': 'Converting video to audio', 'meta': {
                'current': 0,
                'total': 100
            }
        })

        audio_file = convert_video_to_audio(video_file)

        self.update_state(state='PROGRESS', meta={
            'status': 'Transcribing audio to text', 'meta': {
                'current': 10,
                'total': 100
            }
        })

        transcription = transcribe_audio_segments(audio_file)

        self.update_state(state='PROGRESS', meta={
            'status': 'Creating document from text', 'meta': {
                'current': 50,
                'total': 100
            }
        })

        documents, transcript = create_documents_from_transcript(transcription)

        self.update_state(state='PROGRESS', meta={
            'status': 'Summarizing transcript', 'meta': {
                'current': 80,
                'total': 100
            }
        })

        summary = summary_service.summarize_transcript(documents)
        self.update_state(state='PROGRESS', meta={
            'status': 'Transciption and summarization completed', 'meta': {
                'current': 100,
                'total': 100
            }
        })

        result = {
            "summary": summary,
            "summary_word_count": summary_service.calculate_word_count(
                summary),
            "transcript": get_paragraphs(transcription),
            "transcript_word_count": summary_service.calculate_word_count(
                transcript)
        }
        return json.dumps(result)
    except Exception as e:
        raise e
    finally:
        try:
            delete_file(video_file)
            if audio_file:
                delete_file(audio_file)
        except Exception as deletion_error:
            print(str(deletion_error))


@worker.task(bind=True)
def download_and_generate_video_summmary_task(self, link):
    """Background task to download youtube video and
    summarize it and save to db"""
    audio_file = None
    try:
        self.update_state(state='PROGRESS', meta={
            'status': 'Downloading Audio From Youtube', 'meta': {
                'current': 0,
                'total': 100
            }
        })
        audio_file = download_audio_yt(link)
        print(audio_file)
        self.update_state(state='PROGRESS', meta={
            'status': 'Transcribing audio to text', 'meta': {
                'current': 10,
                'total': 100
            }
        })

        transcription = transcribe_audio(audio_file)

        self.update_state(state='PROGRESS', meta={
            'status': 'Creating document from text', 'meta': {
                'current': 20,
                'total': 100
            }
        })

        documents, transcript = create_documents_from_transcript(transcription)

        self.update_state(state='PROGRESS', meta={
            'status': 'Summarizing transcript', 'meta': {
                'current': 70,
                'total': 100
            }
        })

        summary = summary_service.summarize_transcript(documents)

        self.update_state(state='PROGRESS', meta={
            'status': 'Transciption and summarization completed', 'meta': {
                'current': 100,
                'total': 100
            }
        })

        result = {
            "summary": summary,
            "summary_word_count": summary_service.calculate_word_count(
                summary),
            "transcript": get_paragraphs(transcription),
            "transcript_word_count": summary_service.calculate_word_count(
                transcript)
        }
        return json.dumps(result)
    except Exception as e:
        raise e
    finally:
        try:
            if audio_file:
                delete_file(audio_file)
        except Exception as deletion_error:
            print(str(deletion_error))


@worker.task()
def delete_pdf(path):
    try:
        delete_file(path)
    except Exception as deletion_error:
        print(str(deletion_error))
