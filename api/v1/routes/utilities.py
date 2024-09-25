from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import requests, os

from api.utils.files import get_media_type_from_extension
from api.utils.settings import settings
from api.utils.success_response import success_response
from api.v1.schemas.utilities import DownloadRequest, TextTranslateRequest
from api.v1.services.text_translation import translation_service

utilities = APIRouter(tags=["Utilities"])


@utilities.post("/download")
async def download_file(schema: DownloadRequest):
    try:
        # Fetch the file from the URL
        response = requests.get(schema.file_url, stream=True)
        response.raise_for_status()  # Check for errors in the response
        
        file_path = os.path.join(settings.TEMP_DIR, schema.file_url.split("/")[-1])
        with open(file_path, "wb") as video_file:
            for chunk in response.iter_content(chunk_size=8192):
                video_file.write(chunk)

        # Return the file as a FileResponse
        return FileResponse(
            file_path,
            media_type=get_media_type_from_extension(file_path.split(".")[-1]),
            filename=file_path.split('/')[-1]
        )

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Error downloading file: {str(e)}")


@utilities.post('/translate-text')
async def translate_text(schema: TextTranslateRequest):

    translated_text = translation_service.translate_text(
        source_text=schema.text,
        target_language=schema.target_language
    )

    return success_response(
        status_code=200,
        message="Translation successful",
        data={
            'translated_text': translated_text
        }
    )



