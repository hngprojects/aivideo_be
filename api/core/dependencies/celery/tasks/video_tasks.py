import http.client
from celery import shared_task
import json
from sqlalchemy.orm import Session
from api.core.dependencies.celery.celery_app import worker
from api.utils.files import delete_file
from api.v1.services.ai_tools.talking_avatar import talking_avatar_service
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

    return {"video_id": video_id, "video_url": video_url}


@worker.task()
def generate_thumbnails_task(video_id: str, base_url: str, manual_capture: bool = False, timestamp: float = None):
    '''Background task to generate thumbnails'''

    thumbnails = asyncio.run(
        generate_thumbnails_service(
            video_id, base_url, manual_capture, timestamp)
    )
    return thumbnails


@worker.task()
def select_and_download_thumbnail_task(video_id: str, thumbnail_id: str, resolution: str, base_url: str):
    '''Background task to select and download a thumbnail'''

    thumbnail = asyncio.run(
        select_and_download_thumbnail_service(
            video_id, thumbnail_id, resolution, base_url)
    )
    return thumbnail

@shared_task(bind=True)
def create_video_from_text_task(self, text: str, user_id: str):
    """
    Celery task to generate a video from text input.
    Args:
        text_input: The text input data
        user_id: ID of the user who initiated the request
    Returns:
        video_url: The URL of the generated video
    """
    try:
        conn = http.client.HTTPSConnection(app_settings.X_RAPIDAPI_HOST)
        headers = {
            'x-rapidapi-key': app_settings.X_RAPIDAPI_KEY,
            'x-rapidapi-host': app_settings.X_RAPIDAPI_HOST,
            'Content-Type': "application/json"
        }
       
        payload = json.dumps({
            "text_prompt": text,
            'model': "gen3",
            "width": 1344,
            "height": 768,
            "motion": 5,
            "seed": 0,
            "upscale": True,
            "interpolate": True,
            "callback_url": ""
        })
        # Send request to start video generation
        conn.request("POST", "/generate/text", payload, headers)
       
        response = conn.getresponse()
       
        data: dict = json.loads(response.read().decode("utf-8"))
        print("data: ", data)
       
        task_id = data.get('uuid')
        status = data.get('status')
        # store video_url in the database
        video_task = db.query(TextToVideo).filter_by(user_id=user_id).first()
        if not video_task and status and task_id:
            video_task = TextToVideo(
                user_id=user_id,
                status=status,
                task_id=str(task_id)
            )
            db.add(video_task)
            db.commit()
            db.refresh(video_task)
        elif status and task_id:
            video_task.task_id = str(task_id)
            video_task.status = status
            db.commit()
    except Exception as exc:
        self.retry(exc=exc, countdown=120)
        raise exc

@shared_task(bind=True)
def check_video_generate_status(self):
    try:
        conn = http.client.HTTPSConnection(app_settings.X_RAPIDAPI_HOST)
        process_tasks = db.query(TextToVideo).filter_by(status='Task is in queue').all()
        if not process_tasks:
            return
        for task in process_tasks:
            headers = {
                'x-rapidapi-key': app_settings.X_RAPIDAPI_KEY,
                'x-rapidapi-host': app_settings.X_RAPIDAPI_HOST,
            }

            conn.request("GET", f"/status?uuid={task.task_id}", headers=headers)
            response = conn.getresponse()
            data: dict = json.loads(response.read().decode("utf-8"))

            print('data: ', data)
            status = data.get('status')
            task_id = data.get('uuid')
            if status == 'success':
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
        print("error: ", exc)
        self.retry(exc=exc, countdown=120)
        raise exc
