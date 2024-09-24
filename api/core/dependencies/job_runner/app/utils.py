import json
from typing import Optional
from sqlalchemy.orm import Session

from api.v1.models.job import TifiJob
from api.loggers.job_info_logger import job_info_logger


def save_and_print_job_progress(
    db: Session, 
    job: TifiJob, 
    progress: int,
    progress_info: Optional[str] = None
):
    if progress_info:
        print(f'Job {job.id} progress information: {progress_info}')
        job_info_logger.info(f'Job {job.id} progress information: {progress_info}')
        
        job.status_message = progress_info
        db.commit()
        db.refresh(job)
        
    job.progress = f'{progress}% complete'
    db.commit()
    db.refresh(job)

    print(f'Job {job.id} progress: {job.progress}')
    job_info_logger.info(f'Job {job.id} progress: {job.progress}')


def parse_json_string(output: str):
    """Validate that the given output is a valid JSON string. 
    Returns the parsed JSON object if valid, otherwise returns None."""

    try:
        # Attempt to parse the string into JSON
        return json.loads(output)
    except (ValueError, TypeError):
        # Return None if parsing fails (invalid JSON or non-string input)
        return None
