import sys, json
from api.v1.services.ai_tools.script_to_video import ttv_service

payload = json.loads(sys.argv[1])


# Run task
result = ttv_service.process_script(
    script=payload.get('script'),
    scenes=payload.get('scenes'),
    voice_over=payload.get('voice_over'),
    aspect_ratio=payload.get('aspect_ratio'),
    background_audio=payload.get('background_audio', None)
)

print(json.dumps(result))
