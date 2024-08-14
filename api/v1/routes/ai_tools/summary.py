from datetime import timedelta
from fastapi import BackgroundTasks, Depends, status, APIRouter, Response, Request, File, UploadFile
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils.success_response import success_response
from api.utils.files import upload_file
from api.v1.schemas.project import CreateProject
from api.v1.services.project import project_service
from api.v1.services.celery import celery_service
from api.core.dependencies.celery.tasks.summary_tasks import generate_pdf_summary_task

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
    
    # Create project based on task run
    project_schema = CreateProject(
        title='New project',
        project_type='PDF Summarizer',
    )
    project = project_service.create(db=db, schema=project_schema)

    # Create celery task
    celery_service.create_task(task_id=task.id, project_id=project.id)

    return success_response(
        status_code=202,
        message="Summary generation task initiated successfully",
        data={
            "task_id": task.id
        }
    )
