'''This script is to be run to process all jobs'''


import sys, time
from pathlib import Path

# BASE_DIR should point to the directory that contains the 'api' package
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent.parent.parent

# Add BASE_DIR to sys.path
sys.path.insert(0, str(BASE_DIR))

# --------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------

# Print registered tasks
from api.core.dependencies.job_runner.app.job_manager import tool_to_script_mapping

for tool, script in tool_to_script_mapping.items():
    print(f"`{tool}` task registered ----> `{script}`")

print('\n')

# --------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------

import threading
from api.core.dependencies.job_runner.app.async_runner import job_handlers
from api.core.dependencies.job_runner.app.logger import logger


job_available_event = threading.Event()

def job_runner():
    '''Function to run all available jobs'''

    while True:
        # Skip waiting if there are jobs in the database
        if job_handlers.check_available_jobs():  # Check if there are any jobs in the DB
            print("New jobs available in the DB, processing immediately.")
        else:
            # Wait for 60 seconds before runnung jobs
            job_available_event.wait(60)

        try:
            # Process parallel jobs first
            job_handlers.handle_parallel_jobs()

            # Process serial jobs (FFmpeg-like jobs) after parallel jobs are done
            job_handlers.handle_serial_jobs()

            # Reset the event
            job_available_event.clear()

        except Exception as e:
            logger.error(f"Error processing jobs: {e}")
        
        finally:
            # Delay before next execution
            time.sleep(5)


# Start the threads
if __name__ == "__main__":
    # Start the job processing thread
    job_thread = threading.Thread(target=job_runner)
    job_thread.start()

    # Wait for thread to complete execution
    job_thread.join()

    print("All threads have been terminated gracefully.")
    