from typing import Optional
from fastapi import (
    Depends,
    Form,
    status,
    APIRouter,
    HTTPException,
    File,
    UploadFile,
    Request
)
from sqlalchemy.orm import Session
import requests
import io

from api.db.database import get_db
from api.utils.success_response import success_response
from api.utils.files import delete_file, upload_file_to_current_dir, upload_to_temp_dir
from api.utils.minio_service import minio_service
from api.v1.models.project import ProjectToolsEnum
from api.v1.schemas.ai_tools.audio_transcriber import PodcastRequest
from api.v1.services.ai_tools.summary import summary_service
from api.v1.services.job import tifi_job_service
from api.v1.services.user import user_service
from api.utils.tool_limiter import track_tool_usage
from api.v1.models.user import User

summary = APIRouter(prefix="/tools/summary", tags=["Tools"])

MAX_FILE_SIZE = 25 * 1024 * 1024


@summary.post(
    "/pdf-summarizer",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=success_response,
)
@track_tool_usage(ProjectToolsEnum.pdf_summarizer)
async def summarize_pdf(
    request: Request,
    file: UploadFile = File(...),
    detail_level: str = Form(default='short'),
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(user_service.get_current_user_optional)
):
    """Endpoint to summarize PDF"""

    if detail_level not in ['short', 'detailed', 'very short']:
        raise HTTPException(
            status_code=400, 
            detail='Detail level must be one of short, detailed, very short'
        )

    pdf_file_path = await upload_to_temp_dir(
        file,
        allowed_extensions=['pdf'],
        save_extension="pdf",
        max_file_size=20 * 1024 * 1024,
    )

    # Upload pdf file to temporary stirage bucket
    pdf_file_url = minio_service.upload_to_tmp_bucket(source_file=pdf_file_path)
    delete_file(pdf_file_path)

    job = tifi_job_service.create(
        db=db,
        tool_name=ProjectToolsEnum.pdf_summarizer.value,
        payload={'pdf_file_url': pdf_file_url, 'detail_level': detail_level},
        user_id=user.id if user else None,
        is_parallel=True
    )

    return success_response(
        status_code=202,
        message=f"{ProjectToolsEnum.pdf_summarizer.value} task initiated successfully",
        data={
            "job_id": job.id,
            "file_name": file.filename,
        }
    )


@summary.post("/summarize-podcast", status_code=status.HTTP_202_ACCEPTED, response_model=success_response)
@track_tool_usage(ProjectToolsEnum.podcast_summarizer)
async def summarize_podcast(
    schema: PodcastRequest, 
    request: Request,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(user_service.get_current_user_optional)
):

    podcast_details = summary_service.get_podcast_details(schema.podcast_url)
    audio_url = summary_service.get_audio_url(schema.podcast_url)

    audio_response = requests.get(audio_url)
    if audio_response.status_code == 200:
        file_like_object = io.BytesIO(audio_response.content)
        file_like_object.filename = "podcast.mp3"
        file_path = await upload_file_to_current_dir(
            file_like_object, 
            allowed_extensions=['mp3', 'mp4'], 
            save_extension='mp3',
        )

        final_audio_url = minio_service.upload_to_tmp_bucket(source_file=file_path)
        delete_file(file_path)

        job = tifi_job_service.create(
            db=db,
            tool_name=ProjectToolsEnum.podcast_summarizer.value,
            payload={'audio_url': final_audio_url},
            user_id=user.id if user else None,
            is_parallel=True
        )

        return success_response(
            status_code=202,
            message=f"{ProjectToolsEnum.podcast_summarizer.value} task initiated successfully",
            data={
                "job_id": job.id,
                "podcast_details": podcast_details,
            }
        )
    
    else:
        return success_response(
            status_code=404,
            message="Podcast not found",
            data={}
        )

# @summary.post('/audio-summarizer', status_code=status.HTTP_200_OK, response_model=success_response)
# @track_tool_usage(ProjectToolsEnum.audio_summarizer)
# async def summarize_audio(
#     request: Request,
#     file: UploadFile = File(...), 
#     target_lang: str = "es",  # Default to Spanish
#     db: Session = Depends(get_db),
#     user: User = Depends(user_service.get_current_user_optional)
# ):
#     '''Endpoint to summarize an audio file'''
    
#     audio_file = await upload_file(
#         file, 
#         allowed_extensions=['mp3', 'wav'],
#         upload_folder='audio', 
#         save_extension='mp3' 
#     )
#     await check_file_size(file)
    
#     task_transcribe = transcribe_audio_task.delay(audio_file)
#     task = generate_audio_summary_task.delay(audio_file, target_lang)

#     project = job_service.create_project_with_job(
#         job=task,
#         project_title='New Audio Summarization Project',
#         project_type=ProjectToolsEnum.audio_summarizer.value
#     )

#     project_transcribe = job_service.create_project_with_job(
#         job=task_transcribe,
#         project_title='New Audio transcription Project',
#         project_type=ProjectToolsEnum.audio_transcriber.value
#     )

#     return success_response(
#         status_code=202,
#         message="Audio summary generation and transcription  job initiated successfully",
#         data={
#             "job_id": task.id,
#             "project_id": project.id,
#             "transcription_job_id": task_transcribe.id,
#             "transcription_project_id": project_transcribe.id,

#         }
#     )
