'''This script is to be run to process all jobs'''

import sys
import os
from pathlib import Path

# BASE_DIR should point to the directory that contains the 'api' package
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent.parent.parent

# Add BASE_DIR to sys.path
sys.path.insert(0, str(BASE_DIR))


from api.db.database import SessionLocal
from api.core.dependencies.job_runner.app.async_runner import job_handlers

db = SessionLocal()

try:
    # Process parallel jobs first
    job_handlers.handle_parallel_jobs(db)

    # Process serial jobs (FFmpeg-like jobs) after parallel jobs are done
    job_handlers.handle_serial_jobs(db)

finally:
    db.close()
