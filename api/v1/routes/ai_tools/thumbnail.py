from fastapi import APIRouter, File, UploadFile, HTTPException, Request
from api.core.dependencies.celery.tasks.video_tasks import upload_video_task, generate_thumbnails_task
from api.utils.settings import settings
from api.utils.success_response import success_response
from api.utils.files import upload_file
from api.v1.services.job import job_service
from api.v1.schemas.ai_tools.thumbnail import ThumbnailRequest
from urllib.parse import urljoin
import os

thumbnail_router = APIRouter(
    prefix="/tools/thumbnail-generator", tags=["Tools"])


max_file_size = 100 * 1024 * 1024  # 100 MB


@thumbnail_router.post("/upload")
async def upload_video(request: Request, file: UploadFile = File(...)):
    base_url = str(request.base_url)

    file_content = await file.read()
    file_size = len(file_content)

    print(f"Uploaded file size: {file_size} bytes")

    if file_size > max_file_size:
        raise HTTPException(
            status_code=400, detail="File exceeds the maximum allowed size of 100MB."
        )

    saved_path = await upload_file(
        file,
        allowed_extensions=settings.ALLOWED_EXTENSIONS,
        upload_folder='videos',
        save_extension=file.filename.split('.')[-1].lower(),
    )

    video_id = os.path.basename(saved_path).split('.')[0]
    video_url = urljoin(
        base_url, f"media/uploads/videos/{os.path.basename(saved_path)}")

    task = upload_video_task.delay(
        video_id,
        base_url
    )

    project = job_service.create_project_with_job(
        job=task,
        project_title='Video Upload Project',
        project_type='Video Thumbnail Generator'

    )

    return success_response(
        status_code=200,
        message="Video uploaded successfully.",
        data={
            "job_id": task.id,
            "project_id": project.id,
            "video_id": video_id,
            "video_url": video_url
        }
    )


@thumbnail_router.post("/generate-thumbnails")
async def generate_thumbnails(request: Request, body: ThumbnailRequest):
    task = generate_thumbnails_task.delay(
        body.video_id, str(request.url), body.manual_capture, body.timestamp
    )

    thumbnails = task.get()

    project = job_service.create_project_with_job(
        job=task,
        project_title='Thumbnail Generation',
        project_type='Video Thumbnail Generator'
    )

    return success_response(
        status_code=200,
        message="Thumbnails generated successfully.",
        data={
            "job_id": task.id,
            "project_id": project.id,
            "video_id": body.video_id,
            "thumbnail_urls": thumbnails
        }
    )
