from fastapi import File, UploadFile, HTTPException
import os
from pathlib import Path
from api.utils.logger import logging

ALLOWED_EXTENSIONS = {".mp4", ".mp3"}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
BASE_DIR = Path(__file__).resolve().parent.parent.parent


async def upload_video(file: UploadFile = File(...)) -> str:
    # Check file extension
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only MP3 and MP4 files are allowed.",
        )

    # Check file size
    file_size = len(file.file.read())
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Max size is {MAX_FILE_SIZE / (1024 * 1024)} MB.",
        )
    file.file.seek(0)  # Reset file pointer after reading it

    # Save file using BASE_DIR
    video_dir = BASE_DIR / "videos"
    video_dir.mkdir(
        parents=True, exist_ok=True
    )  # Create the directory if it doesn't exist
    file_location = video_dir / file.filename
    with open(file_location, "wb+") as file_object:
        file_object.write(file.file.read())
    logging.info("video processed successfully")
    return str(file_location)
