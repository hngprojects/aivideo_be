from celery import Celery
from celery.schedules import crontab

from api.utils.settings import settings

worker = Celery(
    "worker",
    broker=settings.CELERY_BROKER_URL,
    backend=f"db+{settings.DB_URL}",
    include=[
        'api.core.dependencies.celery.tasks.summary_tasks',
        'api.core.dependencies.celery.tasks.audio_tasks',
        'api.core.dependencies.celery.tasks.video_summary_tasks',
        'api.core.dependencies.celery.tasks.audio_task',
        'api.core.dependencies.celery.tasks.video_tasks',
        'api.core.dependencies.celery.tasks.video_subtitles_tasks',
    ]
)

# Automatically discover tasks from the specified module
worker.autodiscover_tasks(['api.core.dependencies.celery.tasks'], related_name='tasks')

worker.conf.update(
    task_track_started=True,
    beat_schedule={
        'check-video-status-every-1-minutes': {
            'task': 'api.core.dependencies.celery.tasks.video_tasks.check_video_generate_status',
            'schedule': crontab(minute='*/1'),  # every 60 seconds
        },
    },
)

worker.conf.update(task_track_started=True)

if __name__ == "__main__":
    worker.start()


