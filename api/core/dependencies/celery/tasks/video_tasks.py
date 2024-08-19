import requests
from celery import shared_task
import json
from sqlalchemy.orm import Session
from api.core.dependencies.celery.celery_app import worker
from api.utils.files import delete_file
from api.v1.services.ai_tools.talking_avatar import talking_avatar_service
from api.v1.services.ai_tools.text_to_video import ttv_service
from api.v1.services.ai_tools.thumbnail import generate_thumbnails_service, select_and_download_thumbnail_service
from api.utils.settings import settings as app_settings
from api.utils.files import upload_file
from api.db.database import get_db
from api.v1.models import User, TextToVideo
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


@worker.task()
def geenerate_video_from_text_task(script: str):
    '''Background task to generate video from text'''

    data = ttv_service.process_script(script)
    return json.dumps(data)


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
def generate_thumbnails_task(video_id: str, base_url: str, timestamp: float = None):
    '''Background task to generate thumbnails'''

    thumbnails = asyncio.run(
        generate_thumbnails_service(
            video_id, base_url, timestamp)
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

@shared_task(bind=True)
def check_video_generate_status(self):
    try:
        process_tasks = db.query(TextToVideo).filter_by(status='Task is in queue').all()
        if not process_tasks:
            return
        for task in process_tasks:
            
            data, _ = asyncio.run(check_video_status(task.task_id))

            status = data.get('status')
            task_id = data.get('uuid')
            info = data.get('info')
            if status == 'success' or info == 'success':
                video_url = data.get("url")
                gif_url = data.get("gif_url")
                (db.query(TextToVideo)
                .filter_by(task_id=str(task_id))
                .update({
                    "status": status,
                    "video_url": video_url,
                    "gif_url": gif_url
                }))
                db.commit()
    except Exception as exc:
        self.retry(exc=exc, countdown=180)
        raise exc

async def check_video_status(task_id: str):
    """
    Async request
    """
    headers = {
        'x-rapidapi-key': app_settings.X_RAPIDAPI_KEY,
        'x-rapidapi-host': app_settings.X_RAPIDAPI_HOST,
    }
    url = f'https://runwayml.p.rapidapi.com/status?uuid={task_id}'
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return data, response.status_code
    else:
        raise requests.RequestException(f"An error occurred with status code {response.status_code}")