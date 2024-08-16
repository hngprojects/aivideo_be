import json
from api.core.dependencies.celery.celery_app import worker
from api.utils.files import delete_file
from api.v1.services.ai_tools.talking_avatar import talking_avatar_service
from api.v1.services.ai_tools.thumbnail import generate_thumbnails_service, select_and_download_thumbnail_service
from api.utils.settings import settings as app_settings
from api.utils.files import upload_file
from api.db.database import get_db
from uuid import uuid4
import os
import asyncio
from urllib.parse import urljoin

db = next(get_db())


@worker.task()
def generate_talking_avatar_task(
    img_file, 
    audio_file, 
    aspect_ratio, 
    script: str, 
    voice_over, 
    default: bool
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

    return video


@worker.task()
def upload_video_task(video_id: str, base_url: str):
    loop = asyncio.get_event_loop()

    video_folder = os.path.join(app_settings.MEDIA_DIR, 'uploads', 'videos')
    video_filename = None

    for filename in os.listdir(video_folder):
        if filename.startswith(video_id):
            video_filename = filename
            break

    if not video_filename:
        raise FileNotFoundError(
            f"Video with ID {video_id} not found in {video_folder}")

    video_path = os.path.join(video_folder, video_filename)

    video_url = urljoin(base_url, f"media/uploads/videos/{video_filename}")

    return json.dumps({"video_id": video_id, "video_url": video_url})


@worker.task()
def generate_thumbnails_task(video_id: str, base_url: str, manual_capture: bool = False, timestamp: float = None):
    '''Background task to generate thumbnails'''

    thumbnails = asyncio.run(
        generate_thumbnails_service(
            video_id, base_url, manual_capture, timestamp)
    )
    return json.dumps({'thumbnails': thumbnails})


@worker.task()
def select_and_download_thumbnail_task(video_id: str, thumbnail_id: str, resolution: str, base_url: str):
    '''Background task to select and download a thumbnail'''

    thumbnail = asyncio.run(
        select_and_download_thumbnail_service(
            video_id, thumbnail_id, resolution, base_url)
    )
    return thumbnail
