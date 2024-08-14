from api.core.dependencies.celery.celery_app import worker
from api.v1.services.ai_tools.thumbnail import generate_thumbnails_service
from api.utils.settings import settings
from api.utils.files import upload_file


@worker.task()
def upload_video_task(file_data, base_url):
    filename = file_data['filename']
    file_content = file_data['file_content']


    file_path = os.path.join(settings.MEDIA_DIR, 'uploads', 'videos', filename)
    with open(file_path, 'wb') as f:
        f.write(file_content)


    video_id, video_url = upload_file(file_path, base_url)

    return {
        'video_id': video_id,
        'video_url': video_url
    }
# def process_uploaded_video_task(file_path: str, base_url: str):
#     loop = asyncio.get_event_loop()
#     return loop.run_until_complete(generate_thumbnails_service(file_path, base_url, app_settings))


# @worker.task()
# def process_youtube_video_task(youtube_url: str, request):
#     return process_youtube_video_service(youtube_url, request)


# @worker.task()
# def generate_thumbnails_task(video_id: str, manual_capture: bool = False, timestamp: float = None):
#     return generate_thumbnails_service(video_id, manual_capture, timestamp)


# @worker.task()
# def select_and_download_thumbnail_task(video_id: str, selected_thumbnail_id: str):
#     return select_and_download_thumbnail_service(video_id, selected_thumbnail_id)
