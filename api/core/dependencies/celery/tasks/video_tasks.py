from fastapi import HTTPException, status
from typing import List, Optional
import json
from sqlalchemy.orm import Session
from api.core.dependencies.celery.celery_app import worker
from api.utils.files import delete_file
from api.v1.services.ai_tools.yt_summary import yts_service
from api.v1.services.ai_tools.talking_avatar import talking_avatar_service
from api.v1.services.ai_tools.text_to_video import ttv_service
from api.v1.services.ai_tools.thumbnail import generate_thumbnails_service, select_and_download_thumbnail_service
from api.utils.settings import settings
from api.db.database import get_db
import os
import asyncio
import yt_dlp
from urllib.parse import urljoin

db: Session = next(get_db())


@worker.task()
def generate_talking_avatar_task(
    img_file,
    aspect_ratio,
    script: str,
    voice_over,
    default: bool,
    audio_file: Optional[str] = None,
):
    # def generate_talking_avatar_task():
    '''Background task to generate talking avatar and save to database'''

    video = talking_avatar_service.process_script(
        image_file=img_file,
        audio_file=audio_file,
        aspect_ratio=aspect_ratio,
        script=script,
        voice_over=voice_over
    )

    if not default:
        delete_file(img_file)

    return json.dumps(video)


# TEXT TO VIDEO
@worker.task()
def generate_video_scenes_task(script: str):
    '''Background task to generate video scenes'''

    scenes = ttv_service.generate_scene_descriptions(script=script)

    return json.dumps({'scenes': scenes})


@worker.task()
def geenerate_video_from_script_task(
    script: str,
    scenes: List[str],
    voice_over: str,
    aspect_ratio: str,
    background_audio: Optional[str] = None,
):
    '''Background task to generate video from text'''

    data = ttv_service.process_script(
        script=script,
        scenes=scenes,
        background_audio=background_audio,
        voice_over=voice_over,
        aspect_ratio=aspect_ratio,
    )

    return json.dumps(data)

# END TEXT TO VIDEO


@worker.task()
def upload_video_task(video_id: str, base_url: str):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    video_folder = os.path.join(settings.TEMP_DIR)
    print(f"video_folder: {video_folder}")
    video_filename = None

    for filename in os.listdir(video_folder):
        if filename.startswith(video_id):
            video_filename = filename
            break

    if not video_filename:
        raise FileNotFoundError(
            f"Video with ID {video_id} not found in {video_folder}")

    video_path = os.path.join(video_folder, video_filename)
    print(f"video_path: {video_path}")

    video_url = urljoin(base_url, f"tmp/media/{video_filename}")

    return json.dumps({"video_id": video_id, "video_url": video_url})


@worker.task()
def process_youtube_video_task(youtube_url: str, base_url: str):
    # Validate video size before downloading
    max_size_mb = 100  #

    ydl_opts = {'skip_download': True}

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=False)

    video_size_bytes = info.get('filesize') or info.get('filesize_approx', 0)
    video_size_mb = video_size_bytes / (1024 * 1024)

    if video_size_mb > max_size_mb:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"The video exceeds the maximum allowed size of {max_size_mb} MB."
        )

    saved_path = yts_service.download_video(youtube_url)

    print(f"Saved path: {saved_path}")

    video_id = os.path.basename(saved_path).split('.')[0]
    video_url = urljoin(
        base_url, f"/tmp/media/{os.path.basename(saved_path)}")

    return json.dumps({"video_id": video_id, "video_url": video_url})


@worker.task()
def generate_thumbnails_task(video_id: str, base_url: str, aspect_ratio: str, timestamp: float = None, title: str = None):
    '''Background task to generate thumbnails'''
    thumbnails = asyncio.run(
        generate_thumbnails_service(
            video_id, base_url, aspect_ratio, timestamp, title
        )
    )
    return json.dumps({'video_id': video_id, 'thumbnails': thumbnails, 'title': title})


@worker.task()
def select_and_download_thumbnail_task(thumbnail_url: str):
    '''Background task to select and download a thumbnail'''

    thumbnail = asyncio.run(
        select_and_download_thumbnail_service(
            thumbnail_url)
    )
    return json.dumps({"thumbnail": thumbnail})
