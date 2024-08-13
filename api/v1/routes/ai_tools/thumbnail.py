from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from api.v1.schemas.ai_tools.thumbnail import YouTubeVideoRequest, ManualCaptureThumbnailRequest, ThumbnailSelectionRequest
from api.v1.services.ai_tools.thumbnail import upload_video_service, process_youtube_video_service, generate_thumbnails_service, manual_capture_thumbnail_service, select_and_download_thumbnail_service
from api.utils.settings import settings
from api.utils.success_response import success_response

thumbnail_router = APIRouter(prefix="/thumbnails", tags=["Thumbnails"])


@thumbnail_router.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    video_id = await upload_video_service(file, settings)
    return success_response(
        status_code=200,
        message="Video uploaded successfully.",
        data={"video_id": video_id}
    )
