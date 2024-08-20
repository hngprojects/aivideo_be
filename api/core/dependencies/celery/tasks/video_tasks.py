from typing import List
import json
from sqlalchemy.orm import Session
from api.core.dependencies.celery.celery_app import worker
from api.utils.files import delete_file
from api.v1.services.ai_tools.yt_summary import yts_service
from api.v1.services.ai_tools.talking_avatar import talking_avatar_service
from api.v1.services.ai_tools.text_to_video import ttv_service
from api.v1.services.ai_tools.thumbnail import generate_thumbnails_service, select_and_download_thumbnail_service
from api.utils.settings import settings as app_settings
from api.utils.files import delete_file
from api.db.database import get_db
import os
import asyncio
from urllib.parse import urljoin

db: Session = next(get_db())


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
    background_audio: str,
    aspect_ratio: str
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
def process_youtube_video_task(youtube_url: str, base_url: str):

    saved_path = yts_service.download_video(youtube_url)

    print(f"Saved path: {saved_path}")

    video_id = os.path.basename(saved_path).split('.')[0]
    video_url = urljoin(
        base_url, f"/media/downloads/videos/{os.path.basename(saved_path)}")

    return json.dumps({"video_id": video_id, "video_url": video_url})


@worker.task()
def generate_thumbnails_task(video_id: str, base_url: str, timestamp: float = None):
    '''Background task to generate thumbnails'''

    thumbnails = asyncio.run(
        generate_thumbnails_service(
            video_id, base_url, timestamp)
    )

    return json.dumps({'video_id': video_id, 'thumbnails': thumbnails})


@worker.task()
def select_and_download_thumbnail_task(video_id: str, thumbnail_id: str, resolution: str, base_url: str):
    '''Background task to select and download a thumbnail'''

    thumbnail = asyncio.run(
        select_and_download_thumbnail_service(
            video_id, thumbnail_id, resolution, base_url)
    )
    return thumbnail
