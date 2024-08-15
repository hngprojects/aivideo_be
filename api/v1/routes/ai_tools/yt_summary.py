from fastapi import (
    Depends,
    status,
    APIRouter,
    File,
    UploadFile,
)
from sqlalchemy.orm import Session
from api.utils.logger import logging
from api.utils.transcriber import transcribe
from api.utils.pdf_transform import pdf_transform
from api.db.database import get_db
from api.utils.success_response import success_response
from api.utils.videos import upload_video
from api.v1.services.job import job_service
from api.core.dependencies.celery.tasks.video_summary_tasks import (
    generate_video_summary_task,
)

yt_summary = APIRouter(prefix="/tools/summary", tags=["Tools"])


@yt_summary.post(
    "/youtube-summarizer",
    status_code=status.HTTP_200_OK,
    response_model=success_response,
)
async def summarize_yt_vid(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Endpoint to summarize a single youtube video"""

    video = await upload_video(file)
    # Run task

    task = generate_video_summary_task.delay(video)
    logging.info(f"Background task started {task.id}")
    # Create project with job
    project = job_service.create_project_with_job(
        job=task, project_title="New project", project_type="YT video Summarizer"
    )

    return success_response(
        status_code=202,
        message="Summary generation job initiated successfully",
        data={
            "job_id": task.id,
            "project_id": project.id,
        },
    )
