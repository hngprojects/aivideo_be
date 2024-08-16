from fastapi import Depends, status, APIRouter, File, UploadFile, HTTPException
from sqlalchemy.orm import Session

from api.utils.transcriber import transcribe
from api.utils.pdf_transform import pdf_transform
from api.db.database import get_db
from api.utils.success_response import success_response
from api.utils.videos import upload_video
from api.v1.services.job import job_service
from api.core.dependencies.celery.tasks.summary_tasks import generate_yt_transcript
import yt_dlp
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from secrets import token_hex


def download_video(link):
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    video_dir = BASE_DIR / "videos"
    filepth = str(video_dir / f"{token_hex()}.mp4")
    # Ensure the videos directory exists
    if not video_dir.exists():
        video_dir.mkdir(parents=True, exist_ok=True)

    ydl_opts = {
        "outtmpl": filepth,  # Specify the output path and filename as a string
        "format": "worst",  # Download the worst quality format available
    }

    def download_video():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([link])

    # Run the download in a separate thread to avoid blocking
    with ThreadPoolExecutor() as executor:
        future = executor.submit(download_video)
        try:
            future.result()
        except yt_dlp.utils.DownloadError as e:
            raise HTTPException(status_code=500, detail=f"Error downloading video: {e}")
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"An unexpected error occurred: {e}"
            )

    return filepth
