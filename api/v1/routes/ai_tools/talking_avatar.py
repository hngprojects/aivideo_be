from fastapi import Depends, status, APIRouter, File, UploadFile
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils.success_response import success_response
from api.utils.files import upload_file
from api.v1.schemas.project import CreateProject
from api.v1.services.project import project_service
from api.v1.services.celery import celery_service
from api.core.dependencies.celery.tasks.video_tasks import generate_talking_avatar_task

video = APIRouter(prefix="/tools/video", tags=["Video"])

@video.post('/talking-head', status_code=status.HTTP_200_OK, response_model=success_response)
async def talking_avatar(file: UploadFile = File(...), db: Session = Depends(get_db)):
    '''Endpoint to Talking Avatar'''
    file_extension = file.filename.split(".")[-1]
    image_file = await upload_file(
        file, 
        allowed_extensions=['jpg', 'jpeg', 'png'],
        upload_folder='user_avatars', 
        save_extension=file_extension
    )

    # Run task
    task = generate_talking_avatar_task.delay(image_file)
    
    # Create project based on task run
    project_schema = CreateProject(
        title='Video project',
        project_type='Talking Head',
    )
    project = project_service.create(db=db, schema=project_schema)

    # Create celery task
    celery_service.create_task(task_id=task.id, project_id=project.id)

    return success_response(
        status_code=202,
        message="Talking Avatar generation task initiated successfully",
        data={
            "task_id": task.id
        }
    )
