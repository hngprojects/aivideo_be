from api.core.dependencies.celery.celery_app import worker
from api.core.dependencies.job_runner.app.services.regular_service import process_job, run_available_jobs


@worker.task()
def run_job_in_celery(job_id: str):
    '''Background task to run a job in the celery'''

    process_job(job_id)


@worker.task()
def run_available_jobs_in_celery():
    '''Background task to run all pending jobs in the celery'''

    run_available_jobs()
