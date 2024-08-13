from fastapi import HTTPException
import json
from typing import Any, Optional
from sqlalchemy.orm import Session
from api.core.base.services import Service
from api.utils.db_validators import check_model_existence
from api.v1.models.user import User
from api.v1.models.profile import Profile
from api.v1.schemas.profile import ProfileCreateUpdate



class ProfileService(Service):
    '''Profile service functionality'''
    def create():
        pass
    
    def update(self, db: Session, schema: ProfileCreateUpdate, user_id: str):
        '''Updates a Profile, creates one if it doesn't exist'''

        profile = db.query(Profile).filter(Profile.user_id == user_id).first()
        user = db.query(User).filter(User.id == user_id).first()

        if not profile:
            profile_data = schema.dict()
            if "social" in profile_data and isinstance(profile_data["social"], dict):
                profile_data["social"] = json.dumps(profile_data["social"])
            profile = Profile(**profile_data, user_id=user_id)
            db.add(profile)
        else:
            update_data = schema.dict()
            if "social" in update_data and isinstance(update_data["social"], dict):
                update_data["social"] = json.dumps(update_data["social"])

            for key, value in update_data.items():
                setattr(profile, key, value)

        # Update user's email if provided
        if schema.email:
            user.email = schema.email

        # Update avatar URL if provided
        if schema.avatar_url:
            user.avatar_url = schema.avatar_url

        db.commit()
        db.refresh(profile)
        db.refresh(user)

        return profile


    def fetch_by_user_id(
        self, 
        db: Session, 
        user_id: str
    ):
        '''Fetches a profile by user_id'''

        profile = db.query(Profile).filter(Profile.user_id == user_id).first()

        if not profile:
            raise HTTPException(status_code=404, detail="User profile not found")

        return profile



    def fetch_all(
        self, db: Session, 
        **query_params: Optional[Any]
    ):
        '''Fetch all Profiles with optional search parameters'''

        query = db.query(Profile)

        # Enable filter by query parameters
        if query_params:
            for column, value in query_params.items():
                if hasattr(Profile, column) and value:
                    query = query.filter(getattr(Profile, column).ilike(f'%{value}%'))

        return query.all()

    def fetch(
        self, db: Session, 
        id: str
    ):
        '''Fetches a profile by its id'''

        profile = check_model_existence(db, Profile, id)
        return profile

    def delete(
        self, db: Session, 
        id: str
    ):
        '''Deletes a profile'''

        profile = self.fetch(id=id)
        db.delete(profile)
        db.commit()

profile_service = ProfileService()