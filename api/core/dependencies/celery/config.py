from api.utils.settings import settings
from kombu import Queue, Exchange

broker_url = settings.CELERY_BROKER_URL
result_backend = f"db+{settings.DB_URL}"

task_serializer = "json"
result_serializer = "json"
accept_content = ["json"]
timezone = "UTC"
enable_utc = True

# task_queues = (
#     Queue('high', Exchange('high'), routing_key='high'),
#     Queue('normal', Exchange('normal'), routing_key='normal'),
#     Queue('low', Exchange('low'), routing_key='low'),
# )

# # Route tasks to specific queues
# task_routes = {
#     'api.core.dependencies.celery.tasks.summary_tasks.generate_pdf_summary_task': {'queue': 'normal'}
# }

# Result backend settings
result_expires = 3600  # Results will expire after 1 hour

# SQLAlchemy-specific settings
database_table_names = {
    'task': 'celery_taskmeta',
    'groups': 'celery_groupmeta',
}
database_short_lived_sessions = True
