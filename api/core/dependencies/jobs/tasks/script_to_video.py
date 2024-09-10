import sys, json
from api.v1.services.ai_tools.script_to_video import ttv_service
from api.utils.files import delete_file
from api.utils.minio_service import minio_service

payload = json.loads(sys.argv[1])


audio_url = payload.get('audio_url', None)

audio_file = None
if audio_url:
    print(f'Downloading and opening audio file from {audio_url}...')
    audio_file = minio_service.download_file_from_minio(audio_url)


# Run task
result = ttv_service.process_script(
    script=payload.get('script'),
    scenes=payload.get('scenes'),
    voice_over=payload.get('voice_over'),
    aspect_ratio=payload.get('aspect_ratio'),
    background_audio=audio_file
)

if audio_file:
    delete_file(audio_file)
    
print(json.dumps(result))
