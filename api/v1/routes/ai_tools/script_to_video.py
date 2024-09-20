from typing import Optional
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.v1.models.user import User
from api.v1.services.user import user_service
from api.utils.tool_limiter import track_tool_usage
from api.utils.success_response import success_response
from api.v1.services.job import job_service
from api.v1.services.job import tifi_job_service
from api.v1.services.ai_tools.script_to_video import ttv_service
from api.v1.services.presets import preset_service
from api.v1.models.project import ProjectToolsEnum
from api.v1.schemas.ai_tools.script_to_video import SceneGeneration, TTVSchema
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


@ttv_router.post('/text-to-video/generate-scenes', status_code=200, response_model=success_response)
async def generate_video_scenes(
    request: Request,
    schema: SceneGeneration,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(user_service.get_current_user_optional)
):
    '''Endpoint to generate video scenes'''

    scenes = ttv_service.generate_scene_descriptions(script=schema.script)

    return success_response(
        status_code=200,
        message=f"Scenes generated successfully",
        data={
            "scenes": scenes,
        }
    )


@ttv_router.post('/text-to-video/generate-video', status_code=202, response_model=success_response)
@track_tool_usage(ProjectToolsEnum.script_to_video)
async def convert_script_to_video(
    schema: TTVSchema,
    request: Request,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(user_service.get_current_user_optional)
):
    '''Endpoint to convert a script to video'''
    
    if schema.audio_id:
        audio = preset_service.fetch_music_by_id(
            db=db, music_id=schema.audio_id
        )

        audio_url = audio.file_url

    job = tifi_job_service.create(
        db=db,
        tool_name=ProjectToolsEnum.script_to_video.value,
        payload={
            'script': schema.script,
            'scenes': schema.scenes,
            'aspect_ratio': schema.aspect_ratio.lower(),
            'audio_url': audio_url if schema.audio_id else None,
            'voice_over': schema.voice_over.lower(),
        },
        user_id=user.id if user else None,
        is_parallel=False
    )

    return success_response(
        status_code=202,
        message=f"{ProjectToolsEnum.script_to_video.value} task initiated successfully",
        data={
            "job_id": job.id,
            # "project_id": project.id
        }
    )
