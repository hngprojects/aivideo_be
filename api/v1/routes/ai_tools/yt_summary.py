from datetime import timedelta
from fastapi import (
    BackgroundTasks,
    Depends,
    status,
    APIRouter,
    Response,
    Request,
    File,
    UploadFile,
)
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils.success_response import success_response
from api.utils.videos import upload_video
from api.utils.transcriber import transcribe
from api.utils.pdf_transform import pdf_transform
from api.v1.schemas.project import CreateProject
from api.v1.services.project import project_service
from api.v1.services.celery import celery_service
from api.core.dependencies.celery.tasks.summary_tasks import generate_pdf_summary_task

yt_summary = APIRouter(prefix="/tools/summary", tags=["Tools"])


@yt_summary.post(
    "/youtube-summarizer",
    status_code=status.HTTP_200_OK,
    response_model=success_response,
)
async def summarize_yt_vid(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Endpoint to summarize a single youtube video"""

    video = await upload_video(file)
    transcript = await transcribe(video)
    pdf_file = await pdf_transform(transcript)
    # # Run task
    # task = generate_pdf_summary_task.delay(pdf_file)

    # # Create project based on task run
    # project_schema = CreateProject(
    #     title="New project",
    #     project_type="PDF Summarizer",
    # )
    # project = project_service.create(db=db, schema=project_schema)

    # # Create celery task
    # celery_service.create_task(task_id=task.id, project_id=project.id)
    return success_response(
        status_code=202,
        message="Summary generation task initiated successfully",
        data={"task_id": transcript},
    )
