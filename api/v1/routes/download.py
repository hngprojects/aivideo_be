
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import requests

from api.utils.files import get_media_type_from_extension
from api.v1.schemas.ai_tools.talking_avatar import DownloadRequest

download_router = APIRouter(prefix="/download", tags=["Download"])





@download_router.post("")
async def download_file(schema: DownloadRequest):
    try:
        # Fetch the file from the URL
        response = requests.get(schema.file_url, stream=True)
        response.raise_for_status()  # Check for errors in the response
        file_name = f"convey_{schema.file_url.split("/")[-1]}"
        with open(file_name, "wb") as video_file:
            video_file.write(response.content)

        # Return the file as a FileResponse
        return FileResponse(
            file_name,
            media_type=get_media_type_from_extension(file_name.split(".")[-1]),
            filename=file_name
        )

    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error downloading file: {str(e)}"
        )
