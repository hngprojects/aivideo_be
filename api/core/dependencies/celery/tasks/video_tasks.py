from api.core.dependencies.celery.celery_app import worker
from api.utils.files import delete_file
from api.v1.services.ai_tools.talking_avatar import talking_avatar_service

@worker.task()
def generate_talking_avatar_task(img_file, audio_file, aspect_ratio, script, voice_over, default: bool):
# def generate_talking_avatar_task(img_file, aspect_ratio, script, voice_over, default: bool):
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
