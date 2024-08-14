from datetime import timedelta
from fastapi import BackgroundTasks, Depends, status, APIRouter, File, UploadFile
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils.success_response import success_response
from api.utils.files import upload_file
from api.v1.schemas.project import CreateProject
from api.v1.services.project import project_service
from api.v1.services.job import job_service
from api.core.dependencies.celery.tasks.summary_tasks import generate_pdf_summary_task

from datetime import timedelta
from fastapi import BackgroundTasks, Depends, status, APIRouter, File, UploadFile
from sqlalchemy.orm import Session
from api.db.database import get_db
from api.utils.success_response import success_response
from api.utils.files import upload_file
from api.v1.services.job import job_service
from api.v1.schemas.project import CreateProject
from api.v1.services.ai_tools.summary import summary_service
from api.core.dependencies.celery.tasks.summary_tasks import generate_audio_summary_task


summary = APIRouter(prefix="/tools/summary", tags=["Tools"])

@summary.post('/pdf-summarizer', status_code=status.HTTP_200_OK, response_model=success_response)
async def summarize_pdf(file: UploadFile = File(...), db: Session = Depends(get_db)):
    '''Endpoint to summarize PDF'''
    
    pdf_file = await upload_file(
        file, 
        allowed_extensions=['pdf'], 
        upload_folder='pdf', 
        save_extension='pdf'
    )

    # Run task
    task = generate_pdf_summary_task.delay(pdf_file)
    
    # Create project with job
    project = job_service.create_project_with_job(
        job=task,
        project_title='New project',
        project_type='PDF Summarizer'
        # user_id = pass in the current user id for authenticated users
    )

    return success_response(
        status_code=202,
        message="Summary generation job initiated successfully",
        data={
            "job_id": task.id,
            "project_id": project.id,
        }
    )


@summary.post('/audio-summarizer', status_code=status.HTTP_200_OK, response_model=success_response)
async def summarize_audio(
    file: UploadFile = File(...), 
    target_lang: str = "es",  # Default to Spanish
    db: Session = Depends(get_db)
):
    '''Endpoint to summarize an audio file'''
    
    audio_file = await upload_file(
        file, 
        allowed_extensions=['mp3', 'wav'],  # Update allowed extensions as needed
        upload_folder='audio', 
        save_extension=None  # Keep the original extension
    )

    # Run the task for summarizing the audio
    task = generate_audio_summary_task.delay(audio_file, target_lang)
    
    # Create project with job
    project = job_service.create_project_with_job(
        job=task,
        project_title='New Audio Summarization Project',
        project_type='Audio Summarizer'
    )

    return success_response(
        status_code=202,
        message="Audio summary generation job initiated successfully",
        data={
            "job_id": task.id,
            "project_id": project.id,
        }
    )