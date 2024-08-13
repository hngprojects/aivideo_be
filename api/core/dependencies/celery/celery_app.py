from celery import Celery
from api.utils.settings import settings

worker = Celery(
    "worker",
    broker=settings.CELERY_BROKER_URL,
    backend=f'db+{settings.DB_URL}',
    include=['api.core.dependencies.celery.tasks.summary_tasks']
)

worker.conf.update(
    task_track_started=True,
    broker_connection_retry_on_startup=True
)



if __name__ == "__main__":
    worker.start()
