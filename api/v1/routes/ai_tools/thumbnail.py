from fastapi import APIRouter, File, UploadFile, HTTPException, Request
from api.core.dependencies.celery.tasks.video_tasks import upload_video_task
from api.utils.settings import settings
from api.utils.success_response import success_response
from api.utils.files import upload_file
import os
from urllib.parse import urljoin

thumbnail_router = APIRouter(prefix="/thumbnails", tags=["Thumbnails"])


@thumbnail_router.post("/upload")
async def upload_video(request: Request, file: UploadFile = File(...)):
    base_url = str(request.base_url)

    saved_path = await upload_file(
        file,
        allowed_extensions=settings.ALLOWED_EXTENSIONS,
        upload_folder='videos',
        save_extension=file.filename.split('.')[-1].lower(),
        max_file_size=settings.MAX_FILE_SIZE
    )

    video_id = os.path.basename(saved_path).split('.')[0]
    video_url = urljoin(
        base_url, f"media/uploads/videos/{os.path.basename(saved_path)}")

    task = upload_video_task.delay(
        video_id,
        base_url
    )

    return success_response(
        status_code=200,
        message="Video uploaded successfully.",
        data={
            "task_id": task.id,
            "video_id": video_id,
            "video_url": video_url
        }
    )


@thumbnail_router.post("/generate-thumbnails")
async def generate_thumbnails(new_filename):

    thumbnails = await generate_thumbnails_service(new_filename)
    return success_response(
        status_code=200,
        message="Thumbnails generated successfully.",
        data={"thumbnail_ids": thumbnails}
    )
