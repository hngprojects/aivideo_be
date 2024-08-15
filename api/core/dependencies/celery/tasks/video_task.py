from celery import shared_task
import requests
from api.core.dependencies.celery.celery_app import worker
from api.db.database import get_db

db = next(get_db())

@worker.task()
def generate_video_task(text_prompt: str, width: int, height: int, motion: int, seed: int, upscale: bool, interpolate: bool):
    """Background task to generate video from text prompt using RunwayML API."""
    
    url = "https://runwayml.p.rapidapi.com/generate/text"
    payload = {
        "text_prompt": text_prompt,
        "model": "gen3",
        "width": width,
        "height": height,
        "motion": motion,
        "seed": seed,
        "upscale": upscale,
        "interpolate": interpolate,
        "callback_url": ""
    }
    headers = {
        "x-rapidapi-key": "YOUR_RAPIDAPI_KEY",
        "x-rapidapi-host": "runwayml.p.rapidapi.com",
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, json=payload, headers=headers)
    result = response.json()
    
    # Handle the response and save relevant information to the database if needed
    return result
