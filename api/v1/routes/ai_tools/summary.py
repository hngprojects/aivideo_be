from fastapi import Depends, status, APIRouter, File, UploadFile
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils.success_response import success_response
from api.utils.files import upload_file_to_current_dir, delete_file
from api.v1.services.job import job_service
from api.core.dependencies.celery.tasks.summary_tasks import generate_pdf_summary_task

summary = APIRouter(prefix="/tools/summary", tags=["Tools"])

@summary.post('/pdf-summarizer', status_code=status.HTTP_200_OK, response_model=success_response)
async def summarize_pdf(file: UploadFile = File(...), db: Session = Depends(get_db)):
    '''Endpoint to summarize PDF'''
    
    pdf_file = await upload_file_to_current_dir(
        file, 
        allowed_extensions=['pdf'], 
        save_extension='pdf'
    )

    # Run task
    task = generate_pdf_summary_task.delay(pdf_file)
    
    # Create project with job
    project = job_service.create_project_with_job(
        job=task,
        project_title='New project',
        project_type='PDF Summarizer',
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
