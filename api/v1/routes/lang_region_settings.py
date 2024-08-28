from fastapi import Depends, APIRouter, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from typing import List
from api.utils.success_response import success_response
from api.v1.models.user import User
from api.v1.schemas.lang_region_settings import (
    RegionCreate, RegionOut, RegionUpdate
)
from api.db.database import get_db
from api.v1.services.lang_region_settings import region_service
from api.v1.services.user import user_service


regions = APIRouter(prefix="/regions", tags=["Regions, Timezone and Language"])



@regions.put("", response_model=RegionOut, status_code=status.HTTP_200_OK)
def create_or_update_region(
    region: RegionCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(user_service.get_current_user)
):
    region_data = region_service.create_or_update(db, region, current_user.id)
    
    return success_response(
        status_code=status.HTTP_200_OK,
        message='Region created or updated successfully',
        data=region_data['data']
    )


@regions.get("", response_model=RegionOut)
def get_region_by_user(
    db: Session = Depends(get_db), 
    current_user: User = Depends(user_service.get_current_user)
):
    region_data = region_service.fetch(db, current_user.id)
    
    if not region_data:
        return success_response(
            status_code=404,
            message='Region not found',
            data=None
        )
        
        
    
    return success_response(
        status_code=200,
        message='Region retrieved successfully',
        data=region_data['data']
    )
