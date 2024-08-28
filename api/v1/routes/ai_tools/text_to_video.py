from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils.success_response import success_response
from api.v1.services.job import job_service
from api.v1.services.ai_tools.text_to_video import ttv_service
from api.v1.services.presets import preset_service
from api.v1.schemas.project import ProjectToolsEnum
from api.v1.schemas.ai_tools.text_to_video import SceneGeneration, TTVSchema
from api.core.dependencies.celery.tasks.video_tasks import geenerate_video_from_script_task, generate_video_scenes_task


ttv_router = APIRouter(prefix='/tools/video', tags=['Tools'])


@ttv_router.post('/text-to-video/recompose-script', status_code=200, response_model=success_response)
async def recompose_script(
    schema: SceneGeneration,
    db: Session = Depends(get_db)
):
    '''Endpoint to generate video scenes'''

    script = ttv_service.recompose_script(schema.script)

    return success_response(
        status_code=200,
        message="Script recomposed successfully",
        data={
            "script": script,
        }
    )


@ttv_router.post('/text-to-video/generate-scenes', status_code=202, response_model=success_response)
async def generate_video_scenes(
    schema: SceneGeneration,
    db: Session = Depends(get_db)
):
    '''Endpoint to generate video scenes'''

    task = generate_video_scenes_task.delay(schema.script)

    # Create job
    job = job_service.create_job(
        job_id=task.id,
        # user_id = pass in the current user id for authenticated users
    )

    return success_response(
        status_code=202,
        message="Scene generation initiated",
        data={
            "job_id": task.id,
        }
    )

@ttv_router.post('/text-to-video/generate-video', status_code=202, response_model=success_response)
async def convert_text_to_video(
    schema: TTVSchema,
    db: Session = Depends(get_db)
):
    '''Endpoint to convert a script to video'''
    
    if schema.audio_id:
        audio = preset_service.fetch_music_by_id(
            db=db, music_id=schema.audio_id
        )

        audio_file = audio.file_path

    task = geenerate_video_from_script_task.apply_async(kwargs={
        'background_audio': audio_file if schema.audio_id else None,
        'scenes': schema.scenes,
        'aspect_ratio': schema.aspect_ratio,
        'script': schema.script,
        'voice_over': schema.voice_over.lower(),
    })

    # Create project with job
    project = job_service.create_project_with_job(
        job=task,
        project_title='New TTV Project',
        project_type=ProjectToolsEnum.text_to_video.value,
        # user_id = pass in the current user id for authenticated users
    )

    return success_response(
        status_code=202,
        message="Video generation initiated successfully",
        data={
            "job_id": task.id,
            "project_id": project.id
        }
    )
