import json
import time, subprocess
from sqlalchemy.orm import Session
from api.v1.models.job import TifiJob, JobStatus


def poll_for_jobs(db: Session):
    '''This function polls for jobs in the database'''

    while True:

        # Get all premium jobs i.e jobs for a premium user
        premium_pending_jobs = db.query(TifiJob).filter(
            TifiJob.status == JobStatus.pending,
            TifiJob.is_premium == True
        ).all()

        # Get all free jobs i.e jobs for a free user
        free_pending_jobs = db.query(TifiJob).filter(
            TifiJob.status == JobStatus.pending,
            TifiJob.is_premium == False
        ).limit(10).all()

        # Get all jobs
        all_pending_jobs = db.query(TifiJob).filter(TifiJob.status == JobStatus.pending).limit(10).all()

        for job in all_pending_jobs:
            job.status = JobStatus.received
            db.commit()

            process_job(job=job, db=db)

        time.sleep(10)  # poll every two seconds


def process_job(job: TifiJob, db: Session):
    '''This function runs processes a jobo and updates the status of the job'''

    try:
        job.status = JobStatus.progress
        db.commit()

        # Call the tool to process the job
        result = run_job_tool(job)
        
        job.status = JobStatus.completed
        job.result = result
        
    except Exception as e:
        job.status = JobStatus.failed
        job.result = str(e)
    
    db.commit()


def run_job_tool(job: TifiJob, task_name: str):
    '''THis function runs the tool to run the job script for each job'''

    try:
        # Convert the payload to a JSON string
        payload_str = json.dumps(job.payload)

        result = subprocess.run(
            ['python3', f'api/core/dependencies/jobs/{task_name}.py', payload_str],
            capture_output=True, 
            text=True
        )

        # Check if the tool execution was successful
        if result.returncode == 0:
            print(result.stdout)
            return result.stdout
        else:
            raise Exception(f"Job failed: {result.stderr}")
    except subprocess.CalledProcessError as e:
        raise Exception(f"Job failed: {str(e)}")

