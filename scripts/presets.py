import os
from pathlib import Path
from uuid_extensions import uuid7

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


# def load_billing_plans_in_db():
#     '''Function to load all billing plan presets in the database'''

#     plans = [
#         {
#             "plan_name": "Free",
#             "price": 0.00,
#             "plan_interval": "monthly",
#             "currency": "USD",
#             "features": ["Basic support", "Access to community"],
#             "access_limit": 30
#         },
#         {
#             "plan_name": "Basic",
#             "price": 9.99,
#             "plan_interval": "monthly",
#             "currency": "USD",
#             "features": ["Email support", "Access to all features", "Basic analytics"],
#             "access_limit": 100
#         },
#         {
#             "plan_name": "Pro",
#             "price": 29.99,
#             "plan_interval": "monthly",
#             "currency": "USD",
#             "features": ["Priority support", "Access to all features", "Advanced analytics", "Custom reporting"],
#             "access_limit": 300
#         }
#     ]

#     for plan_data in plans:
#         if not db.query(BillingPlan).filter(BillingPlan.plan_name==plan_data["plan_name"]).first():
#             plan = BillingPlan(**plan_data)
#             db.add(plan)
#             db.commit()

