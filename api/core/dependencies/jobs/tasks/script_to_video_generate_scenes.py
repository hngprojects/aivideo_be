import sys, json
from api.v1.services.ai_tools.script_to_video import ttv_service

payload = json.loads(sys.argv[1])


# Run task
result = ttv_service.generate_scene_descriptions(
    script=payload.get('script')
)

print(json.dumps(result))
