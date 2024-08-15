from celery import Celery
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
        'api.core.dependencies.celery.tasks.video_tasks'
    ],
    # task_cls='eventlet'
)

worker.conf.update(task_track_started=True)
if __name__ == "__main__":
    worker.start()


