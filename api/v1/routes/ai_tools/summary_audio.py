from datetime import timedelta
from fastapi import BackgroundTasks, Depends, status, APIRouter, File, UploadFile
from sqlalchemy.orm import Session
from api.db.database import get_db
from api.utils.success_response import success_response
from api.utils.files import upload_file
from api.v1.services.job import job_service
from api.v1.schemas.project import CreateProject
from api.v1.services.ai_tools.summary_audio import summary_service
from api.core.dependencies.celery.tasks.audio_tasks import generate_audio_summary_task, transcribe_audio_task

summary_audio = APIRouter(prefix="/tools/summary", tags=["Tools"])

@summary_audio.post('/audio-summarizer', status_code=status.HTTP_200_OK, response_model=success_response)
async def summarize_audio(
    file: UploadFile = File(...), 
    target_lang: str = "es",  # Default to Spanish
    db: Session = Depends(get_db)
):
    '''Endpoint to summarize an audio file'''
    
    audio_file = await upload_file(
        file, 
        allowed_extensions=['mp3', 'wav'],
        upload_folder='audio', 
        save_extension='mp3'  # Keep the original extension
    )
    audio_data = await file.read()
    task_transcribe = transcribe_audio_task.delay(audio_data)

    # Run the task for summarizing the audio
    task = generate_audio_summary_task.delay(audio_file, target_lang)
    
    # Create project with job
    project = job_service.create_project_with_job(
        job=task,
        project_title='New Audio Summarization Project',
        project_type='Audio Summarizer'
    )

    project_transcribe = job_service.create_project_with_job(
        job=task_transcribe,
        project_title='New Audio transcription Project',
        project_type='Audio transcriber'
    )

    return success_response(
        status_code=202,
        message="Audio summary generation and transcription  job initiated successfully",
        data={
            "job_id": task.id,
            "project_id": project.id,
            "transcription_job_id": task_transcribe.id,
            "transcription_project_id": project_transcribe.id,

        }
    )
