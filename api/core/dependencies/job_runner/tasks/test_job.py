import sys, json, time

from api.db.database import get_db
from api.v1.services.job import tifi_job_service
from api.core.dependencies.job_runner.app.utils import save_and_print_job_progress

db = next(get_db())

payload = json.loads(sys.argv[1])

job_id = payload.get('job_id', None)
job = tifi_job_service.fetch(db, job_id)

try:
    print(payload.get('text', None))
    
    save_and_print_job_progress(db, job, 0, 'Job started')
    time.sleep(5)

    save_and_print_job_progress(db, job, 10)
    time.sleep(5)
    
    save_and_print_job_progress(db, job, 20)
    time.sleep(5)
    
    save_and_print_job_progress(db, job, 30)
    time.sleep(5)
    
    save_and_print_job_progress(db, job, 40)
    time.sleep(5)
    
    save_and_print_job_progress(db, job, 50)
    time.sleep(5)
    
    save_and_print_job_progress(db, job, 60)
    time.sleep(5)
    
    save_and_print_job_progress(db, job, 70)
    time.sleep(5)
    
    save_and_print_job_progress(db, job, 80)
    time.sleep(10)
    
    save_and_print_job_progress(db, job, 90)
    time.sleep(10)

    print(json.dumps({"status": "Job has been executed"}))

except Exception as e:
    raise e
