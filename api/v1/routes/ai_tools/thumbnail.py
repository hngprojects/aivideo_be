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

    # Read the file content asynchronously
    file_content = await file.read()

    # Create a dictionary to pass to the Celery task
    file_data = {
        "filename": file.filename,
        "file_content": file_content
    }

   
    task = upload_video_task.delay(file_data, base_url)

    # Get the task result
    result = task.get(timeout=None)

    return success_response(
        status_code=200,
        message="Video upload task initiated.",
        data={
            "task_id": task.id,
            "video_id": result["video_id"],
            "video_url": result["video_url"]
        }
    )

