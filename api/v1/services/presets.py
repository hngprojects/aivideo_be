import os, random
from pathlib import Path
from secrets import token_hex
from typing import Any, Optional
import openai
from sqlalchemy.orm import Session

from api.utils.settings import settings
from api.utils.minio_service import minio_service
from api.utils import mime_types
from api.v1.models.presets import Avatar, BackgroundMusic, Voice, BackgroundImage
from api.utils.db_validators import check_model_existence
from api.v1.services.tools.general_video_service import video_service


BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
AVATAR_FOLDER = 'presets/avatars'
BACKGROUND_MUSIC_FOLDER = 'presets/background_music'
VOICE_FOLDER = 'presets/voices'
BACKGROUND_IMAGE_FOLDER = 'presets/background_images'

class PresetService:
    '''Preset service functionality'''
    
    # --------------- AVATARS ---------------
    # ---------------------------------------
    
    def load_avatars_in_db(self, db: Session):
        '''Function to load all avatar presets as static files in the database'''
        
        # Load avatar voices in db fiest
        self.load_voices_in_db(db)

        for root, dir, files in os.walk(AVATAR_FOLDER):
            for file_name in files:
                file_path = os.path.join(root, file_name)
                gender = file_name.split('-')[-1].replace('.png', '')                
                voices = None

                # Check if avatar already exists in the database
                if not db.query(Avatar).filter(Avatar.file_name==file_name).first():
                    # Fetch voices from db
                    if gender == 'man':
                        voices = db.query(Voice).filter(Voice.gender=='man').all()
                        
                    elif gender == 'woman':
                        voices = db.query(Voice).filter(Voice.gender=='woman').all()
                    
                    voice_id = random.choice(voices).id
                    
                    # Upload file to minio
                    file_url, download_url = minio_service.upload_to_minio(
                        folder_name='preset-avatars',
                        source_file=file_path,
                        destination_file=file_name,
                        content_type=mime_types.IMAGE_PNG
                    )

                    # Store URL in database
                    avatar = Avatar(
                        file_url=file_url,
                        file_name=file_name,
                        file_path=file_path,
                        # gender=gender
                        voice_id=voice_id
                    )

                    db.add(avatar)
                    db.commit()
                    db.refresh(avatar)
    
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
        
    
    def generate_avatars(self, db: Session):
        '''Generates new avatar images'''

        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        
        gender = ['man', 'woman']
        choice = random.choice(gender)

        response = client.images.generate(
            model="dall-e-3",
            prompt=f"Generate one hyper-realistic headshot image of a {choice} human avatar",
            size="1024x1024",
            quality="standard",
            n=1,
        )
        image_url = response.data[0].url

        file_name = f"avatar-{token_hex(5)}-{choice}.png"
        save_path = os.path.join(BASE_DIR, 'presets', 'avatars', file_name)

        video_service.download_file(
            url=image_url, 
            save_path=save_path
        )

        # Upload file to minio
        file_url, download_url = minio_service.upload_to_minio(
            folder_name='preset-avatars',
            source_file=save_path,
            destination_file=file_name,
            content_type=mime_types.IMAGE_PNG
        )

        # Check if avatar already exists in the database
        avatar = Avatar(
            file_url=file_url,
            file_name=file_name,
            file_path=f'{AVATAR_FOLDER}/{file_name}',
            gender=choice
        )

        db.add(avatar)
        db.commit()
        db.refresh(avatar)

        return avatar

    
    # --------------- AUDIO -----------------
    # ---------------------------------------

    def load_music_in_db(self, db: Session):
        '''Function to load all audio presets as static files in the database'''

        for root, dir, files in os.walk(BACKGROUND_MUSIC_FOLDER):
            for file_name in files:
                # file_url = f'{settings.APP_URL}/{BACKGROUND_MUSIC_FOLDER}/{file_name}'
                file_path = os.path.join(root, file_name)

                # Check if audio already exists in the database
                if not db.query(BackgroundMusic).filter(BackgroundMusic.file_name==file_name).first():
                    # Upload file to minio
                    file_url, download_url = minio_service.upload_to_minio(
                        folder_name='preset-audio',
                        source_file=file_path,
                        destination_file=file_name,
                        content_type=mime_types.AUDIO_MP3
                    )

                    # Store URL in database
                    audio = BackgroundMusic(
                        file_url=file_url,
                        file_name=file_name,
                        file_path=file_path
                    )

                    db.add(audio)
                    db.commit()
                    db.refresh(audio)

    
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
        
    
    # --------------- VOICES ----------------
    # ---------------------------------------
    
    def load_voices_in_db(self, db: Session):
        '''Function to load all voice presets as static files in the database'''

        for root, dir, files in os.walk(VOICE_FOLDER):
            for file_name in files:
                file_path = os.path.join(root, file_name)
                name = file_name.split('-')[0]
                gender = file_name.split('-')[1]

                # Check if voice already exists in the database
                if not db.query(Voice).filter(Voice.file_name==file_name).first():
                    # Upload file to minio
                    file_url, download_url = minio_service.upload_to_minio(
                        folder_name='preset-voices',
                        source_file=file_path,
                        destination_file=file_name,
                        content_type=mime_types.AUDIO_MP3
                    )

                    # Store URL in database
                    voice = Voice(
                        file_url=file_url,
                        file_name=file_name,
                        file_path=file_path,
                        name=name,
                        gender=gender
                    )

                    db.add(voice)
                    db.commit()
                    db.refresh(voice)
    
    def fetch_all_voices(self, db: Session, **query_params: Optional[Any]):
        """Fetch all voices with option to search using query parameters"""

        query = db.query(Voice)

        # Enable filter by query parameter
        if query_params:
            for column, value in query_params.items():
                if hasattr(Voice, column) and value:
                    query = query.filter(getattr(Voice, column).ilike(f"%{value}%"))

        return query.all()
    

    def fetch_voice_by_id(self, db: Session, voice_id: str):
        """Fetches an voice by id"""

        voice = check_model_existence(db, Voice, voice_id)
        return voice


    def delete_voice(self, db: Session, voice_id: str):
        """Deletes an voice"""

        voice = self.fetch_voice_by_id(db, voice_id)
        db.delete(voice)
        db.commit()


    def delete_all_voices(self, db: Session):
        """Deletes all voices from the db"""

        db.query(Voice).delete()
        db.commit()
    
    # ------------- BG IMAGES ---------------
    # ---------------------------------------
    
    def load_background_images_in_db(self, db: Session):
        '''Function to load all background_image presets as static files in the database'''

        for root, dir, files in os.walk(BACKGROUND_IMAGE_FOLDER):
            for file_name in files:
                file_path = os.path.join(root, file_name)

                # Check if background_image already exists in the database
                if not db.query(BackgroundImage).filter(BackgroundImage.file_name==file_name).first():
                    # Upload file to minio
                    file_url, download_url = minio_service.upload_to_minio(
                        folder_name='preset-background-images',
                        source_file=file_path,
                        destination_file=file_name,
                        content_type=mime_types.IMAGE_PNG
                    )

                    # Store URL in database
                    background_image = BackgroundImage(
                        file_url=file_url,
                        file_name=file_name,
                        file_path=file_path,
                    )

                    db.add(background_image)
                    db.commit()
                    db.refresh(background_image)
    
    def fetch_all_background_images(self, db: Session, **query_params: Optional[Any]):
        """Fetch all background_images with option to search using query parameters"""

        query = db.query(BackgroundImage)

        # Enable filter by query parameter
        if query_params:
            for column, value in query_params.items():
                if hasattr(BackgroundImage, column) and value:
                    query = query.filter(getattr(BackgroundImage, column).ilike(f"%{value}%"))

        return query.all()
    

    def fetch_background_image_by_id(self, db: Session, background_image_id: str):
        """Fetches an background_image by id"""

        background_image = check_model_existence(db, BackgroundImage, background_image_id)
        return background_image


    def delete_background_image(self, db: Session, background_image_id: str):
        """Deletes an background_image"""

        background_image = self.fetch_background_image_by_id(db, background_image_id)
        db.delete(background_image)
        db.commit()


    def delete_all_background_images(self, db: Session):
        """Deletes all background_images from the db"""

        db.query(BackgroundImage).delete()
        db.commit()
        

preset_service = PresetService()
