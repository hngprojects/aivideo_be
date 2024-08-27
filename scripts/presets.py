import os
from pathlib import Path
from fastapi import HTTPException
from api.v1.models.billing_plan import BillingPlan

from api.utils.settings import settings
from api.db.database import get_db
from api.v1.models.presets import Avatar, BackgroundMusic

db = next(get_db())

BASE_DIR = Path(__file__).resolve().parent.parent

def load_avatars_in_db():
    '''Function to load all avatar presets as static files in the database'''

    AVATAR_FOLDER = 'presets/avatars'

    for root, dir, files in os.walk(AVATAR_FOLDER):
        for file_name in files:
            file_url = f'{settings.APP_URL}/{AVATAR_FOLDER}/{file_name}'
            file_path = os.path.join(root, file_name)

            # Check if avatar already exists in the database
            if not db.query(Avatar).filter(Avatar.file_name==file_name).first():
                # Store URL in database
                avatar = Avatar(
                    file_url=file_url,
                    file_name=file_name,
                    file_path=file_path
                )

                db.add(avatar)
                db.commit()
                db.refresh(avatar)


def load_audio_in_db():
    '''Function to load all audio presets as static files in the database'''

    MUSIC_FOLDER = 'presets/audio'

    for root, dir, files in os.walk(MUSIC_FOLDER):
        for file_name in files:
            file_url = f'{settings.APP_URL}/{MUSIC_FOLDER}/{file_name}'
            file_path = os.path.join(root, file_name)

            # Check if avatar already exists in the database
            if not db.query(BackgroundMusic).filter(BackgroundMusic.file_name==file_name).first():
                # Store URL in database
                audio = BackgroundMusic(
                    file_url=file_url,
                    file_name=file_name,
                    file_path=file_path
                )

                db.add(audio)
                db.commit()
                db.refresh(audio)



def load_billing_plans_in_db():

    try:
        free_plan = BillingPlan(
            plan_name="Free",
            price=0,
            access_limit=50,
            plan_interval='one-off',
            currency='USD',
            features=[
                'Access to tools',
                'Text to Video',
                'Image to Video',
                'Talking Avatar Generator',
                'Youtube Summarizer',
                'Podcast Summarizer',
                'Limited Processing',
                'Watermark on videos'
            ]
        )

        premium_monthly_plan = BillingPlan(
            plan_name="Premium Monthly",
            price=4.99,
            plan_interval='monthly',
            access_limit=150,
            currency='USD',
            features=[
                'Access to tools',
                'Text to Video',
                'Image to Video',
                'Talking Avatar Generator',
                'Youtube Summarizer',
                'Podcast Summarizer',
                'Watermark free videos',
                'Early access to new features',
                'Early access to future tools'
            ]
        )

        premium_yearly_plan = BillingPlan(
            plan_name="Premium Yearly",
            price=49.99,
            plan_interval='yearly',
            access_limit=500,
            currency='USD',
            features=[
                'Access to tools',
                'Text to Video',
                'Image to Video',
                'Talking Avatar Generator',
                'Youtube Summarizer',
                'Podcast Summarizer',
                'Watermark free videos',
                'Early access to new features',
                'Early access to future tools',
                'Save 15% compared to monthly'
            ]
        )

        db.add(free_plan)
        db.add(premium_monthly_plan)
        db.add(premium_yearly_plan)
        db.commit()

        return db.query(BillingPlan).all()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")
    finally:
        db.close()
