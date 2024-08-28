from typing import Any, Optional, Dict
from sqlalchemy.orm import Session
from api.core.base.services import Service
from api.v1.models.lang_reg_timezone_setting import LanguageRegionTimezoneSetting
from api.v1.schemas.lang_region_settings import RegionUpdate, RegionCreate
from api.utils.db_validators import check_model_existence


class RegionService(Service):
    """Region Services"""
    
    def create(self, db: Session, schema: RegionUpdate, user_id: str) -> Dict[str, Any]:
        '''Basic implementation of create'''
        raise NotImplementedError("The create method is not implemented.")

    
    def create_or_update(self, db: Session, schema: RegionCreate, user_id: str) -> Dict[str, Any]:
        '''Create or Update a Region based on user_id'''

        # Check if a region exists for the user
        region = db.query(LanguageRegionTimezoneSetting).filter_by(user_id=user_id).first()
        

        if region:
            # Update the existing region
            update_data = schema.dict(exclude_unset=True)
            for key, value in update_data.items():
                setattr(region, key, value)
        else:
            # Create a new region
            region = LanguageRegionTimezoneSetting(**schema.dict(), user_id=user_id)
            db.add(region)
        
        db.commit()
        db.refresh(region)

        # Prepare the response data
        response_data = {
            "region": region.region,
            "timezone": region.timezone,
            "language": region.language
        }

        return {'data': response_data}



    def fetch(self, db: Session, user_id: str) -> Optional[Dict[str, Any]]:
        '''Fetches a Region by user_id'''

        region = db.query(LanguageRegionTimezoneSetting).filter_by(user_id=user_id).first()

        if region:
            response_data = {
                "region": region.region,
                "timezone": region.timezone,
                "language": region.language
            }
            return {'data': response_data}

        return None

    
    
    
    def update(self, db: Session, schema: RegionCreate, user_id: str) -> Dict[str, Any]:
        '''Create a new Region'''
        pass
    

    def fetch_all(self, db: Session, **query_params: Optional[Any]) -> Dict[str, Any]:
        '''Fetch all Region with option to search using query parameters'''
        pass
    

    def delete(self, db: Session, region_id: str) -> Dict[str, Any]:
        '''Deletes a region service'''
        pass
    
    
    
region_service = RegionService()

