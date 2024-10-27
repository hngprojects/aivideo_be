import sys, json, os
from uuid import uuid4

from api.v1.services.tools.script_to_video import ttv_service
from api.utils.files import delete_file
from api.v1.services.tools.general_video_service import video_service
from api.v1.services.tools.tweet_to_tiktok import tweet_to_tiktok_service
from api.db.database import get_db
from api.utils.minio_service import minio_service
from api.utils.settings import settings
from api.utils import mime_types
from api.v1.services.job import tifi_job_service
from api.core.dependencies.job_runner.app.utils import save_and_print_job_progress


db = next(get_db())

payload = json.loads(sys.argv[1])

job_id = payload.get('job_id', None)
job = tifi_job_service.fetch(db, job_id)

save_and_print_job_progress(db, job, 0, 'Job started')

audio_url = payload.get('audio_url', None)

background_audio = None
if audio_url:
    save_and_print_job_progress(db, job, 10, f'Downloading and opening audio file from {audio_url}')
    background_audio = minio_service.download_file_from_minio(audio_url)

script = payload.get('text')
media_urls = payload.get('scene_media_urls')
voice_over = payload.get('voice_over')
video_style = payload.get('video_style')

try:
    save_and_print_job_progress(db, job, 15, 'Generating audio from script')
    audio_file = tweet_to_tiktok_service.generate_audio(script, voice_over)
    
    save_and_print_job_progress(db, job, 20, 'Generating subtitle file from generated audio')
    subtitles_file = tweet_to_tiktok_service.generate_subtitles(audio_file)
    
    if video_style == 'talking avatar':
        # TODO: Implement talking avatar logic here
        pass
    else:
        save_and_print_job_progress(db, job, 25, 'Downloading media files')
        media_files = tweet_to_tiktok_service.download_media(media_urls)

        save_and_print_job_progress(db, job, 45, 'Generating images for scenes')
        video_file = tweet_to_tiktok_service.compose_video(audio_file, media_files)

    save_and_print_job_progress(db, job, 60, 'Embedding subtitles in generated video')
    video_with_subtitles = tweet_to_tiktok_service.add_subtitles_to_video(subtitles_file, video_file)

    save_and_print_job_progress(db, job, 65, 'Resizing video')
    final_video_file = tweet_to_tiktok_service.resize_video(video_with_subtitles)

    if background_audio:
        save_and_print_job_progress(db, job, 70, 'Applying background music to the video')
        # Add background music to video
        video_with_audio = video_service.add_background_audio(
            video_path=video_with_subtitles, 
            audio_path=background_audio, 
        )

    save_and_print_job_progress(db, job, 80, 'Cleaning up')
    # Delete unnecessary files
    delete_file(audio_file)
    delete_file(subtitles_file)
    delete_file(video_file)
    delete_file(video_with_subtitles)
    if background_audio:
        delete_file(video_with_audio)

    # save_url = f'{settings.APP_URL}/{final_result_file}'

    save_and_print_job_progress(db, job, 85, 'Generating preview and download links for generated video')
    minio_save_file = f'twttotiktk-{str(uuid4().hex)}.mp4'
    save_url, download_url = minio_service.upload_to_minio(
        folder_name='tweet-to-tiktok',
        source_file=final_video_file,
        destination_file=minio_save_file,
        content_type=mime_types.VIDEO_MP4
    )

    save_and_print_job_progress(db, job, 90, 'Generating result and final cleanup')
    result = {
        "url": save_url,
        "download_url": download_url,
    }

    delete_file(final_video_file)

    save_and_print_job_progress(db, job, 95)

    print(json.dumps(result))

except Exception as e:
    raise e

finally:
    if background_audio:
        delete_file(background_audio)
