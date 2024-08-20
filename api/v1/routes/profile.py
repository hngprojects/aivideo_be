from fastapi import Depends, APIRouter, status, Form
from sqlalchemy.orm import Session
import os
import shutil
from typing import Optional


from api.v1.models.user import User
from api.v1.schemas.profile import ProfileBase, ProfileCreateUpdate
from api.db.database import get_db
from api.v1.services.user import user_service
from api.v1.services.profile import profile_service
from fastapi import UploadFile, File
from api.utils.success_response import success_response


profile = APIRouter(prefix='/profile', tags=['Profiles'])


UPLOAD_DIR = "media/uploads/user_avatars"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@profile.get("/me", response_model=success_response)
def get_current_user_profile(
    db: Session = Depends(get_db), 
    current_user: User = Depends(user_service.get_current_user)
    ):
    """
    Get the profile of the currently authenticated user
    """
    profile = profile_service.fetch_by_user_id(db, user_id=current_user.id)
    
    return success_response(
        status_code=status.HTTP_200_OK,
        message="User Profile retrieved Successfully!!!",
        data=profile
    )



@profile.put('', status_code=status.HTTP_200_OK, response_model=ProfileBase)
def update_user_profile(
    username: Optional[str] = Form(None),
    job_title: Optional[str] = Form(None),
    pronouns: Optional[str] = Form(None),
    social: Optional[str] = Form(None),
    phone_number: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    bio: Optional[str] = Form(None),
    avatar: Optional[UploadFile] = File(None),    
    db: Session = Depends(get_db),
    current_user: User = Depends(user_service.get_current_user)
):
    '''Endpoint to update user profile'''
    
    # Construct the schema manually using the validated data
    schema = ProfileCreateUpdate(
        username=username,
        job_title=job_title,
        pronouns=pronouns,
        social=social,
        phone_number=phone_number,
        email=email,
        bio=bio,
    )
    
    
    if avatar:
        filename = f"{current_user.id}_{avatar.filename}"
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        # Check if there is an existing avatar URL and remove the old file
        if current_user.avatar_url:
            old_filename = os.path.basename(current_user.avatar_url)
            old_file_path = os.path.join(UPLOAD_DIR, old_filename)
            
            # Delete the old avatar file if it exists and is different from the new one
            if os.path.exists(old_file_path) and old_filename != filename:
                os.remove(old_file_path)
        
        # Save the new avatar file to the server
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(avatar.file, buffer)
        
        # Generate the URL or path for the saved file
        avatar_url = f"/presets/avatars/{filename}"
        
        current_user.avatar_url = avatar_url
        db.commit()
        db.refresh(current_user)
    
    # Update the user profile and related user data
    updated_profile = profile_service.update(db, schema=schema, user_id=current_user.id)
    
    return success_response(
        status_code=status.HTTP_200_OK,
        message="User Profile Updated Successfully!!!",
        data=updated_profile
    )