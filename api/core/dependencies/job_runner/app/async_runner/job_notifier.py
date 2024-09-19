import requests
from api.utils.settings import settings


def notify_job_runner():
    url = f"{settings.JOB_APP_URL}/notify-job"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            print("Job runner notified successfully")
        elif response.status_code == 202:
            print("Job queued in job runner")
        else:
            print(f"Failed to notify job runner: {response.status_code}")
    except Exception as e:
        print(f"Error notifying job runner: {e}")
