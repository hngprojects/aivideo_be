import sys, json
from api.v1.services.ai_tools.talking_avatar import talking_avatar_service


payload = json.loads(sys.argv[1])

# Run task
result = talking_avatar_service.process_script(
    image_file=payload.get('image_file'),
    aspect_ratio=payload.get('aspect_ratio'),
    script=payload.get('script'),
    voice_over=payload.get('voice_over'),
    audio_file=payload.get('audio_file', None)
)

print(json.dumps(result))
