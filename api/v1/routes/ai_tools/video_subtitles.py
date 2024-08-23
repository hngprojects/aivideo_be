from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form
from typing import Optional
from api.utils.files import upload_file
from api.utils.success_response import success_response
from api.core.dependencies.celery.tasks.video_subtitles_tasks import (
    transcribe_video_task,
    translate_text_task,
    generate_subtitles_task,
)
from api.v1.schemas.video_subtitles import TranslationRequest
from api.v1.services.job import job_service

video_subtitles_router = APIRouter(
    prefix="/tools/video-subtitles", tags=["Tools"])


@video_subtitles_router.post("/translate", status_code=status.HTTP_200_OK, response_model=success_response)
async def translate(request: TranslationRequest):
    try:
        task = translate_text_task.delay(
            request.transcription, request.target_language)

        # Create project with job
        project = job_service.create_project_with_job(
            job=task,
            project_title='New Translation Project',
            project_type='Text Translation'
        )

        return success_response(
            status_code=200,
            message="Text translation job initiated successfully",
            data={
                "job_id": task.id,
                "project_id": project.id,
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@video_subtitles_router.post("/transcribe", status_code=status.HTTP_200_OK, response_model=success_response)
async def transcribe(
    file: UploadFile = File(...),
):
    try:
        # Upload and save the video file
        video_file_path = await upload_file(file, allowed_extensions=['mp4', 'mov', 'avi'], upload_folder="videos")

        # Call the transcription task
        task = transcribe_video_task.delay(video_file_path)

        # Create project with job
        project = job_service.create_project_with_job(
            job=task,
            project_title='New Transcription Project',
            project_type='Video Transcription'
        )

        return success_response(
            status_code=200,
            message="Transcription job initiated successfully",
            data={
                "job_id": task.id,
                "project_id": project.id,
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@video_subtitles_router.post("/generate_subtitles", status_code=status.HTTP_200_OK, response_model=success_response)
async def generate_subtitle( file: UploadFile = File(...)):
    try:
        # Save uploaded video file
        video_file_path = await upload_file(
            file=file,
            allowed_extensions=['mp4', 'mov', 'avi', 'mkv', 'wmv'],
            upload_folder="videos",
            save_extension=file.filename.split('.')[-1]
        )

        # Initiate Celery task
        task = generate_subtitles_task.delay(video_file_path)

        # Create project with job
        project = job_service.create_project_with_job(
            job=task,
            project_title='New Subtitle Generation Project',
            project_type='Subtitle Generation'
        )

        return success_response(
            status_code=200,
            message="Subtitle generation job initiated successfully",
            data={
                "job_id": task.id,
                "project_id": project.id,
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
