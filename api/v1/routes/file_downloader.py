from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import requests, os

from api.utils.files import get_media_type_from_extension
from api.utils.settings import settings
from api.v1.schemas.ai_tools.talking_avatar import DownloadRequest

downloader = APIRouter(prefix="/download", tags=["Download"])


@downloader.post("")
async def download_file(schema: DownloadRequest):
    try:
        # Fetch the file from the URL
        response = requests.get(schema.file_url, stream=True)
        response.raise_for_status()  # Check for errors in the response
        
        file_path = os.path.join(settings.TEMP_DIR, schema.file_url.split("/")[-1])
        with open(file_path, "wb") as video_file:
            video_file.write(response.content)

        # Return the file as a FileResponse
        return FileResponse(
            file_path,
            media_type=get_media_type_from_extension(file_path.split(".")[-1]),
            filename=file_path.split('/')[-1]
        )

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Error downloading file: {str(e)}")
