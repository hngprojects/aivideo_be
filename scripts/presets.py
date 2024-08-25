import os
from pathlib import Path

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
