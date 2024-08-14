from typing import Any, Optional
from sqlalchemy.orm import Session
from api.v1.models.presets import Avatar, BackgroundMusic
from api.utils.db_validators import check_model_existence


class PresetService:
    '''Preset service functionality'''

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


preset_service = PresetService()
