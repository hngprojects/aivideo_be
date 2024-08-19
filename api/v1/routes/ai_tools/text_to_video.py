from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils.success_response import success_response
from api.v1.services.job import job_service
from api.v1.schemas.ai_tools.text_to_video import ScriptSchema
from api.core.dependencies.celery.tasks.video_tasks import geenerate_video_from_text_task


ttv_router = APIRouter(prefix='/tools/video', tags=['Tools'])


@ttv_router.post('/text-to-video', status_code=202, response_model=success_response)
async def convert_text_to_video(
    schema: ScriptSchema,
    db: Session = Depends(get_db)
):
    '''Endpoint to convert a script to video'''
    
    task = geenerate_video_from_text_task.delay(schema.script)

    # Create project with job
    project = job_service.create_project_with_job(
        job=task,
        project_title='New TTV Project',
        project_type='Text to Video',
        # user_id = pass in the current user id for authenticated users
    )

    return success_response(
        status_code=202,
        message="Talking Avatar generation task initiated successfully",
        data={
            "job_id": task.id,
            "project_id": project.id
        }
    )
