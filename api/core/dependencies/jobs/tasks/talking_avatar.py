import sys, json
from api.utils.files import delete_file
from api.utils.minio_service import minio_service
from api.v1.services.ai_tools.talking_avatar import talking_avatar_service


payload = json.loads(sys.argv[1])

image_url = payload.get('image_url')
audio_url = payload.get('audio_url', None)

# Download image and audio files from minio
print(f'Downloading and opening image file from {image_url}...')
image_file = minio_service.download_file_from_minio(image_url)

audio_file = None
if audio_url:
    print(f'Downloading and opening audio file from {audio_url}...')
    audio_file = minio_service.download_file_from_minio(audio_url)


# Run task
result = talking_avatar_service.process_script(
    image_file=image_file,
    aspect_ratio=payload.get('aspect_ratio'),
    script=payload.get('script'),
    voice_over=payload.get('voice_over'),
    audio_file=audio_file
)

delete_file(image_file)
delete_file(audio_file)

print(json.dumps(result))
