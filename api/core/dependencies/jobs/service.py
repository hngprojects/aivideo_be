import json, os, sys
from pathlib import Path
import time, subprocess
from datetime import datetime

from api.core.dependencies.jobs.runner import tool_to_script_mapping
from api.db.database import get_db, SessionLocal
from api.v1.schemas.project import CreateProject
from api.v1.services.project import project_service
from api.v1.services.job import tifi_job_service
from api.v1.models.job import TifiJob, JobStatus


BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent


def run_pending_jobs():
    '''This function checks for and runs all pending jobs in the database'''

    # db = next(get_db())

    while True:
        with SessionLocal() as db:
            current_time = datetime.now().replace(tzinfo=None)

            # Get all premium jobs i.e jobs for a premium user
            premium_pending_jobs = db.query(TifiJob).filter(
                TifiJob.status == JobStatus.pending,
                TifiJob.is_premium == True,
                TifiJob.expiration_time >= current_time,
            ).all()

            # Get all free jobs i.e jobs for a free user
            free_pending_jobs = db.query(TifiJob).filter(
                TifiJob.status == JobStatus.pending,
                TifiJob.is_premium == False,
                TifiJob.expiration_time >= current_time,
            ).limit(5).all()

            # Get all jobs
            all_pending_jobs = db.query(TifiJob).filter(
                TifiJob.status == JobStatus.pending,
                TifiJob.expiration_time >= current_time,
            ).all()

            
            no_of_jobs = len(all_pending_jobs)
            if no_of_jobs > 0:

                for job_obj in all_pending_jobs:
                    try:
                        job_obj.status = JobStatus.received
                        job_obj.progress = '20% complete'
                        db.commit()
                        db.refresh(job_obj)
                        process_job(job_id=job_obj.id)
                    except Exception as e:
                        print(f"Error processing job {job_obj.id}: {e}")
                    
                    time.sleep(2)
            else:
                print('No pending jobs available')
                
            break


def process_job(job_id: str):
    '''This function processes a job and updates the status of the job'''

    db = next(get_db())

    # Fetch job
    job = tifi_job_service.fetch(db=db, job_id=job_id)

    try:
        job.status = JobStatus.progress
        job.progress = '50% complete'
        db.commit()

        output = execute_job(job)

        job.status = JobStatus.completed
        job.result = json.loads(output)
        job.progress = '100% complete'

        # ------- PROJECT PROCESSING -------
        if job.project_id:
            # Get project
            project = project_service.fetch(db, job.project_id)
        else:
            # Create project for user
            project = project_service.create(
                db=db,
                schema=CreateProject(
                    title=f"New {job.tool_name} Project",
                    project_type=job.tool_name,
                    user_id=job.user_id
                )
            )

            # Link created project to the corresponding job
            job.project_id = project.id

        # Update project result
        project.result = json.loads(output)
        project.is_active = True

        db.commit()

    except Exception as e:
        job.status = JobStatus.failed
        job.progress = 'Job failed'
        job.result = {"error": f"{str(e)}"}
        db.commit()
        raise Exception(f'An exception occured: {str(e)}')


def execute_job(job: TifiJob):
    '''THis function runs the tool to run the job script for each job'''

    try:

        # Convert the payload to a JSON string
        payload_str = json.dumps(job.payload)

        # Get script path based on the task name
        script_path = tool_to_script_mapping.get(job.tool_name, None)

        if not script_path:
            raise ValueError(f"No script found for tool: {job.tool_name}")

        # Set PYTHONPATH in environment variables to the root directory
        env = os.environ.copy()
        env["PYTHONPATH"] = BASE_DIR

        process = subprocess.Popen(
            ['python3', '-u', script_path, payload_str],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            bufsize=1
        )

        # Stream output in real-time
        result_output = ''
        for line in iter(process.stdout.readline, ''):
            result_output = line.strip()  # get the last line printed out to the console

        # Ensure the process is finished
        process.stdout.close()
        return_code = process.wait()

        # If there's an error, capture stderr and raise an exception
        if return_code != 0:
            stderr_output = process.stderr.read()
            process.stderr.close()
            # raise Exception(f"Job failed with error: {stderr_output}")   

        return result_output
    
    except subprocess.CalledProcessError as e:
        raise
    except Exception as e:
        raise
