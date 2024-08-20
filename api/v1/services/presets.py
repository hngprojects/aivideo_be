import os
from pathlib import Path
from secrets import token_hex
from typing import Any, Optional
from uuid import uuid4
import openai
from sqlalchemy.orm import Session
from api.utils.settings import settings
from api.v1.models.presets import Avatar, BackgroundMusic
from api.utils.db_validators import check_model_existence
from api.v1.services.ai_tools.general_video_service import video_service


BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
AVATAR_FOLDER = 'presets/avatars'
MUSIC_FOLDER = 'presets/audio'

class PresetService:
    '''Preset service functionality'''
    
    def load_avatars_in_db(db: Session):
        '''Function to load all avatar presets as static files in the database'''

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


    def load_audio_in_db(db: Session):
        '''Function to load all audio presets as static files in the database'''


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

    def fetch_all_avatars(self, db: Session, **query_params: Optional[Any]):
        """Fetch all avatars with option to search using query parameters"""

        query = db.query(Avatar)

        # Enable filter by query parameter
        if query_params:
            for column, value in query_params.items():
                if hasattr(Avatar, column) and value:
                    query = query.filter(getattr(Avatar, column).ilike(f"%{value}%"))

        return query.all()

    def fetch_avatar_by_id(self, db: Session, avatar_id: str):
        """Fetches an avatar by id"""

        avatar = check_model_existence(db, Avatar, avatar_id)
        return avatar

    def delete_avatar(self, db: Session, avatar_id: str):
        """Deletes an avatar"""

        avatar = self.fetch_avatar_by_id(db, avatar_id)
        db.delete(avatar)
        db.commit()

    def delete_all_avatars(self, db: Session):
        """Deletes all avatars from the db"""

        db.query(Avatar).delete()
        db.commit()

    
    def fetch_all_background_music(self, db: Session, **query_params: Optional[Any]):
        """Fetch all background music with option to search using query parameters"""

        query = db.query(BackgroundMusic)

        # Enable filter by query parameter
        if query_params:
            for column, value in query_params.items():
                if hasattr(BackgroundMusic, column) and value:
                    query = query.filter(getattr(BackgroundMusic, column).ilike(f"%{value}%"))

        return query.all()

    def fetch_music_by_id(self, db: Session, music_id: str):
        """Fetches a music by id"""

        music = check_model_existence(db, BackgroundMusic, music_id)
        return music

    def delete_music(self, db: Session, music_id: str):
        """Deletes a music"""

        music = self.fetch_music_by_id(db, music_id)
        db.delete(music)
        db.commit()

    def delete_all_music(self, db: Session):
        """Deletes all music from the db"""

        db.query(BackgroundMusic).delete()
        db.commit()

    def generate_avatars(self, db: Session):
        '''Generates new avatar images'''

        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

        response = client.images.generate(
            model="dall-e-3",
            prompt=f"Generate one hyper-realistic headshot image of a human avatar",
            size="1024x1024",
            quality="standard",
            n=1,
        )
        image_url = response.data[0].url

        file_name = f"avatar-{token_hex(5)}.png"
        save_path = os.path.join(BASE_DIR, 'presets', 'avatars', file_name)

        video_service.download_file(
            url=image_url, 
            save_path=save_path
        )

        file_url = f'{settings.APP_URL}/{AVATAR_FOLDER}/{file_name}'

        # Check if avatar already exists in the database
        avatar = Avatar(
            file_url=file_url,
            file_name=file_name,
            file_path=AVATAR_FOLDER/{file_name}
        )

        db.add(avatar)
        db.commit()
        db.refresh(avatar)

        return avatar


preset_service = PresetService()
