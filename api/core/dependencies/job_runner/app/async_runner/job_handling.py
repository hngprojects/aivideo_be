from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import asc

from api.db.database import SessionLocal
from api.v1.models.job import TifiJob, JobStatus
from api.core.dependencies.job_runner.app.async_runner.thread_config import db_lock, parallel_executor
from api.core.dependencies.job_runner.app.services import regular_service, yield_service

def handle_parallel_jobs(db: Session):
    '''This function handles jobs that can be processed in parallel to each other'''

    current_time = datetime.now()  # Get current time

    # Get all jobs
    parallel_jobs = db.query(TifiJob).filter(
        TifiJob.status == JobStatus.pending,
        TifiJob.expiration_time >= current_time,
        TifiJob.is_parallel == True
    ).order_by(asc(TifiJob.created_at)).all()

    if not parallel_jobs:
        print('No parallel jobs available')
        return

    print('Running parallel jobs')
    
    futures = []
    
    # Submit jobs to ThreadPoolExecutor
    for job in parallel_jobs:
        futures.append(parallel_executor.submit(regular_service.process_job, job.id))

    # Wait for all parallel jobs to complete
    for future in futures:
        future.result()
    
    print('All parallel jobs completed')


def handle_serial_jobs(db: Session):
    '''This function handles heavy jobs that mus be processed one by one'''

    current_time = datetime.now()  # Get current time

    serial_jobs = db.query(TifiJob).filter(
        TifiJob.status == JobStatus.pending,
        TifiJob.expiration_time >= current_time,
        TifiJob.is_parallel == False
    ).order_by(asc(TifiJob.created_at)).all()

    if not serial_jobs:
        print('No serial jobs available')
        return

    print('Running serial jobs')

    # Process serial jobs one by one
    for job in serial_jobs:
        with db_lock:
            regular_service.process_job(job.id)
    
    print('All serial jobs processed')
    

def process_all_jobs():
    """Main job processing function."""

    # Create a database session for each request
    # This ensures that each request gets a fresh session,
    # preventing data from being shared between requests
    # and allowing for proper cleanup of resources when done.

    # Create a lock for managing database transactions
    # This ensures that only one thread can access the database at a time,
    # preventing conflicts and data corruption.

    db = SessionLocal()

    try:
        # Process parallel jobs first
        handle_parallel_jobs(db)

        # Process serial jobs (FFmpeg-like jobs) after parallel jobs are done
        handle_serial_jobs(db)

    finally:
        db.close()