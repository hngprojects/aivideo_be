"""Tasks that handle video transcription and summarization"""
from api.utils.files import delete_file
from api.core.dependencies.celery.celery_app import worker
import json
from api.v1.services.ai_tools.yt_summary import yts_service
from api.v1.services.ai_tools.summary import summary_service


@worker.task(bind=True)
def generate_video_summary_task(self, video_file):
    """Background task to summarize a video and save to database"""

    try:
        self.update_state(state='PROGRESS', meta={
            'status': 'Transcribing video', 'meta': {
                'current': 0,
                'total': 100
            }
        })
        transcription = summary_service.transcribe_audio(video_file)

        self.update_state(state='PROGRESS', meta={
            'status': 'Transcribing video', 'meta': {
                'current': 50,
                'total': 100
            }
        })
        documents = summary_service.create_documents(transcription)

        self.update_state(state='PROGRESS', meta={
            'status': 'Transcribing video', 'meta': {
                'current': 55,
                'total': 100
            }
        })

        summary = summary_service.summarize_transcript(documents)
        self.update_state(state='PROGRESS', meta={
            'status': 'Transcribing video', 'meta': {
                'current': 100,
                'total': 100
            }
        })

        result = {
            "summary": summary,
            "summary_word_count": summary_service.calculate_word_count(summary),
            "transcript": transcription,
            "transcript_word_count": summary_service.calculate_word_count(transcription)
        }
        return json.dumps(result)
    except Exception as e:
        raise e
    finally:
        try:
            delete_file(video_file)
        except Exception as deletion_error:
            print(str(deletion_error))


@worker.task(bind=True)
def download_and_generate_video_summmary_task(self, link):
    """Background task to download youtube video and
    summarize it and save to db"""
    try:
        self.update_state(state='PROGRESS', meta={
            'status': 'Downloading video', 'meta': {
                'current': 0,
                'total': 100
            }
        })
        video_file = yts_service.download_video(link)

        self.update_state(state='PROGRESS', meta={
            'status': 'Transcribing video', 'meta': {
                'current': 10,
                'total': 100
            }
        })

        transcription = summary_service.transcribe_audio(video_file)
        self.update_state(state='PROGRESS', meta={
            'status': 'Converting To Text For Summarizing', 'meta': {
                'current': 50,
                'total': 100
            }
        })

        documents = summary_service.create_documents(transcription)
        self.update_state(state='PROGRESS', meta={
            'status': 'Summarizing video', 'meta': {
                'current': 55,
                'total': 100
            }
        })

        summary = summary_service.summarize_transcript(documents)
        self.update_state(state='PROGRESS', meta={
            'status': 'Completed Summary and Transcription', 'meta': {
                'current': 100,
                'total': 100
            }
        })

        result = {
            "summary": summary,
            "summary_word_count": summary_service.calculate_word_count(summary),
            "transcript": transcription,
            "transcript_word_count": summary_service.calculate_word_count(transcription)
        }
        return json.dumps(result)
    except Exception as e:
        raise e
    finally:
        try:
            delete_file(video_file)
        except Exception as deletion_error:
            print(str(deletion_error))
        # Re-raise the exception after handling cleanup


@worker.task()
def delete_pdf(path):
    try:
        delete_file(path)
    except Exception as deletion_error:
        print(str(deletion_error))
