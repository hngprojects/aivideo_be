from api.core.dependencies.celery.celery_app import worker
from api.v1.services.ai_tools.talking_avatar import talking_avatar_service
from api.db.database import get_db
from uuid import uuid4

db = next(get_db())

@worker.task()
def generate_talking_avatar_task(img_file):
    '''Background task to generate talking avatar and save to database'''
    image_type = "square"  # Choose from 'square', 'vertical', or 'horizontal'
    script_text = "Hello, this is your talking avatar! JO and Bami have been working so hard to build me. THanks  Guys!!"

    video = talking_avatar_service.process_script(
        img_file,
        image_type,
        script_text
    )

    return video


