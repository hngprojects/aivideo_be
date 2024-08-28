import os
import requests
import uuid
import random
from fastapi import HTTPException, status
import subprocess
from api.utils.files import delete_file
from api.utils.settings import settings
from urllib.parse import urljoin
from api.v1.services.ai_tools.general_video_service import GeneralVideoService


async def generate_thumbnails_service(video_id: str, base_url: str, aspect_ratio: str, timestamp: float = None, title: str = None):
    '''Generate thumbnails for a video'''
    base_name = video_id if title is None else title
    video_dirs = [
        os.path.join(settings.TEMP_DIR),
        os.path.join(settings.TEMP_DIR)
    ]

    video_path = None
    for video_dir in video_dirs:
        video_files = os.listdir(video_dir)
        for file in video_files:
            if video_id in file:
                possible_path = os.path.join(video_dir, file)
                video_path = os.path.abspath(possible_path)
                break
        if video_path:
            break

    if not video_path or not os.path.isfile(video_path):
        raise FileNotFoundError(
            f"Video file not found for video_id {video_id}")

    thumbnail_dir = os.path.join(
        settings.MEDIA_DIR, 'downloads', 'thumbnails')
    os.makedirs(thumbnail_dir, exist_ok=True)

    thumbnail_urls = []

    aspect_ratio_service = GeneralVideoService()
    aspect_ratio_dimensions = aspect_ratio_service.set_aspect_ratio(
        aspect_ratio)

    if timestamp is not None:
        thumbnail_id = str(uuid.uuid4())
        output_path = os.path.join(
            thumbnail_dir, f'{base_name}_thumbnail_{thumbnail_id}.jpg'
        )

        temp_thumbnail_path = os.path.join(
            thumbnail_dir, f'{base_name}_temp_thumbnail_{thumbnail_id}.jpg')
        result = subprocess.run(['ffmpeg', '-i', video_path, '-ss',
                                 str(timestamp), '-vframes', '1', temp_thumbnail_path],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error generating manual thumbnail."
            )

        aspect_ratio_service.change_aspect_ratio(
            temp_thumbnail_path, output_path, aspect_ratio)

        os.remove(temp_thumbnail_path)

        thumbnail_url = urljoin(
            base_url, f"/media/downloads/thumbnails/{os.path.basename(output_path)}")
        thumbnail_urls.append(thumbnail_url)
    else:
        ffprobe_command = ['ffprobe', '-v', 'error', '-show_entries',
                           'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', video_path]
        result = subprocess.run(
            ffprobe_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving video duration."
            )

        duration = float(result.stdout.decode().strip())
        random_timestamps = sorted(
            [random.uniform(0, duration) for _ in range(3)])

        for timestamp in random_timestamps:
            thumbnail_id = str(uuid.uuid4())
            output_path = os.path.join(
                thumbnail_dir, f'{base_name}_thumbnail_{thumbnail_id}.jpg'
            )

            temp_thumbnail_path = os.path.join(
                thumbnail_dir, f'{base_name}_temp_thumbnail_{thumbnail_id}.jpg')
            result = subprocess.run(['ffmpeg', '-i', video_path, '-ss',
                                     str(timestamp), '-vframes', '1', temp_thumbnail_path],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode != 0:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Error generating thumbnail."
                )

            aspect_ratio_service.change_aspect_ratio(
                temp_thumbnail_path, output_path, aspect_ratio)

            os.remove(temp_thumbnail_path)

            thumbnail_url = urljoin(
                base_url, f"/media/downloads/thumbnails/{os.path.basename(output_path)}")
            thumbnail_urls.append(thumbnail_url)

    if video_path and os.path.isfile(video_path):
        delete_file(video_path)

    return thumbnail_urls


async def select_and_download_thumbnail_service(thumbnail_url: str) -> str:
    try:

        response = requests.get(thumbnail_url)
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Thumbnail URL not reachable."
            )

        thumbnail_filename = thumbnail_url.split('/')[-1]

        thumbnail_dir = os.path.join(
            settings.MEDIA_DIR, 'downloads', 'thumbnails')
        os.makedirs(thumbnail_dir, exist_ok=True)

        output_path = os.path.join(thumbnail_dir, thumbnail_filename)
        with open(output_path, 'wb') as thumbnail_file:
            thumbnail_file.write(response.content)

        return thumbnail_url

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to select and download thumbnail: {str(e)}"
        )
