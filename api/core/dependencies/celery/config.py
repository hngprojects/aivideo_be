from api.utils.settings import settings
from kombu import Queue, Exchange

broker_url = settings.CELERY_BROKER_URL
result_backend = f"db+{settings.DB_URL}"

task_serializer = "json"
result_serializer = "json"
accept_content = ["json"]
timezone = "UTC"
enable_utc = True

# Result backend settings
result_expires = 3600  # Results will expire after 1 hour

# SQLAlchemy-specific settings
database_table_names = {
    'task': 'celery_taskmeta',
    'groups': 'celery_groupmeta',
}
database_short_lived_sessions = True
