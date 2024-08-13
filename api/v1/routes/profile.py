from fastapi import Depends, APIRouter, status
from sqlalchemy.orm import Session

from api.v1.models.user import User
from api.v1.schemas.profile import ProfileBase, ProfileCreateUpdate
from api.db.database import get_db
from api.v1.services.user import user_service
from api.v1.services.profile import profile_service
from api.utils.success_response import success_response


profile = APIRouter(prefix='/profile', tags=['Profiles'])

@profile.put('', status_code=status.HTTP_200_OK, response_model=ProfileBase)
def update_user_profile(
    schema: ProfileCreateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(user_service.get_current_user)
):
    '''Endpoint to update user profile'''
    
    # Update the user profile and related user data
    updated_profile = profile_service.update(db, schema=schema, user_id=current_user.id)
    
    return success_response(
        status_code=status.HTTP_200_OK,
        message="User Profile Updated Successfully!!!",
        data=updated_profile
    )
