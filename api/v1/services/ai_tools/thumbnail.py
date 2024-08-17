import os
import uuid
from fastapi import HTTPException, status
import subprocess
from typing import List
from api.utils.settings import settings
from urllib.parse import urljoin


async def generate_thumbnails_service(video_id: str, base_url: str, manual_capture: bool = False, timestamp: float = None):
    '''Generate thumbnails for a video'''
    base_name = video_id
    video_files = os.listdir(os.path.join(
        settings.MEDIA_DIR, 'uploads', 'videos'))
    possible_path = os.path.join(
        settings.MEDIA_DIR, 'uploads', 'videos', video_files[0])
    video_path = os.path.abspath(possible_path)

    if not os.path.isfile(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    thumbnail_dir = os.path.join(
        settings.MEDIA_DIR, 'downloads', 'thumbnails')
    os.makedirs(thumbnail_dir, exist_ok=True)

    thumbnail_urls = []

    if manual_capture and timestamp is not None:
        thumbnail_id = str(uuid.uuid4())
        output_path = os.path.join(
            thumbnail_dir, f'{base_name}_thumbnail_{thumbnail_id}.jpg'
        )
        result = subprocess.run(['ffmpeg', '-i', video_path, '-ss',
                                 str(timestamp), '-vframes', '1', output_path],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error generating manual thumbnail."
            )
        thumbnail_url = urljoin(
            base_url, f"/media/downloads/thumbnails/{os.path.basename(output_path)}")
        thumbnail_urls.append(thumbnail_url)
    else:
        ffprobe_command = ['ffprobe', '-v', 'error', '-show_entries',
                           'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', video_path]
        print(f"Running ffprobe command: {' '.join(ffprobe_command)}")
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
             '-of', 'default=noprint_wrappers=1:nokey=1', video_path],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        if result.returncode != 0:
            error_output = result.stderr.decode().strip()
            print(f"ffprobe error: {error_output}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving video duration."
            )

        duration = float(result.stdout.decode().strip())

        for i in range(4):
            timestamp = duration * (i + 1) / 5
            thumbnail_id = str(uuid.uuid4())
            output_path = os.path.join(
                thumbnail_dir, f'{base_name}_thumbnail_{thumbnail_id}.jpg'
            )

            result = subprocess.run(['ffmpeg', '-i', video_path, '-ss',
                                     str(timestamp), '-vframes', '1', output_path],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode != 0:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Error generating thumbnail."
                )

            thumbnail_url = urljoin(
                base_url, f"/media/downloads/thumbnails/{os.path.basename(output_path)}")
            thumbnail_urls.append(thumbnail_url)

    return thumbnail_urls


async def select_and_download_thumbnail_service(video_id: str, thumbnail_id: str, resolution: str, base_url: str) -> str:
    try:
        base_name = video_id
        thumbnail_dir = os.path.join(
            settings.MEDIA_DIR, 'downloads', 'thumbnails')
        input_path = os.path.join(
            thumbnail_dir, f'{base_name}_thumbnail_{thumbnail_id}.jpg'
        )
        output_path = os.path.join(
            thumbnail_dir, f"{base_name}_thumbnail_{thumbnail_id}_{resolution}.jpg"
        )

        resolution_map = {
            "1080": "1920:1080",
            "720": "1280:720",
            "480": "854:480",
            "360": "640:360"
        }

        size = resolution_map.get(resolution)
        if not size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid resolution"
            )

        result = subprocess.run(
            ['ffmpeg', '-i', input_path, '-vf', f'scale={size}', output_path],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        if result.returncode != 0:

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error resizing thumbnail to resolution {resolution}. {result.stderr.decode()}"
            )

        return os.path.join(base_url, f"/media/downloads/thumbnails/{os.path.basename(output_path)}")

    except Exception as e:

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to select and download thumbnail: {str(e)}"
        )
