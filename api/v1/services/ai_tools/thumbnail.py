import os
import uuid
from fastapi import UploadFile, HTTPException
from secrets import token_hex
import yt_dlp
import subprocess
from typing import List
from api.utils.settings import settings
from api.utils.files import upload_file, download_file


async def upload_video_service(file: UploadFile, settings) -> str:

    if len(await file.read()) > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400, detail="File exceeds size limit"
        )

    file.file.seek(0)

    file_extension = file.filename.split('.')[-1].lower()
    if file_extension not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, detail="Invalid file extension"
        )
    new_filename = f'{file.filename.split(".")[0]}-{token_hex(5)}.{file_extension}'
    video_path = os.path.join(settings.MEDIA_DIR, 'uploads', new_filename)

    if os.path.exists(video_path):
        raise HTTPException(
            status_code=400, detail="Video already exists"
        )

    upload_folder = os.path.join(settings.MEDIA_DIR, 'uploads')
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

    saved_path = await upload_file(
        file,
        allowed_extensions=settings.ALLOWED_EXTENSIONS,
        upload_folder='videos',
        save_extension=file_extension
    )

    return os.path.basename(saved_path).split('.')[0]



