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


async def generate_thumbnails_service(new_filename: str) -> List[str]:
    try:

        base_name, file_extension = os.path.splitext(new_filename)
        file_extension = file_extension.lstrip(
            '.')

        video_path = os.path.join(
            settings.MEDIA_DIR, 'uploads', 'videos', f'{new_filename}')

        if not os.path.isfile(video_path):
            raise HTTPException(
                status_code=404, detail="Video file not found.")

        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
             '-of', 'default=noprint_wrappers=1:nokey=1', video_path],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        if result.returncode != 0:
            raise HTTPException(
                status_code=500, detail="Error retrieving video duration.")

        duration = float(result.stdout.decode().strip())

        # Ensure thumbnail directory exists
        thumbnail_dir = os.path.join(
            settings.MEDIA_DIR, 'downloads', 'thumbnails')
        os.makedirs(thumbnail_dir, exist_ok=True)

        thumbnail_ids = []
        for i in range(4):
            timestamp = duration * (i + 1) / 5
            thumbnail_id = str(uuid.uuid4())
            output_path = os.path.join(
                thumbnail_dir, f'{base_name}_thumbnail_{thumbnail_id}.jpg')

            result = subprocess.run(['ffmpeg', '-i', video_path, '-ss',
                                    str(timestamp), '-vframes', '1', output_path],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode != 0:

                raise HTTPException(
                    status_code=500, detail="Error generating thumbnail.")

            thumbnail_ids.append(thumbnail_id)

        return thumbnail_ids

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate thumbnails: {str(e)}")
