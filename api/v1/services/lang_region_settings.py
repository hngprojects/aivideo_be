from typing import Any, Optional, Dict
from sqlalchemy.orm import Session
from api.core.base.services import Service
from api.v1.models.lang_reg_timezone_setting import LanguageRegionTimezoneSetting
from api.v1.schemas.lang_region_settings import RegionUpdate, RegionCreate
from api.utils.db_validators import check_model_existence


class RegionService(Service):
    """Region Services"""

    def create(self, db: Session, schema: RegionCreate, user_id: str) -> Dict[str, Any]:
        '''Create a new Region'''

        new_region = LanguageRegionTimezoneSetting(**schema.model_dump(), user_id=user_id)
        db.add(new_region)
        db.commit()
        db.refresh(new_region)
        
        # Response data
        response_data = {
            "region": new_region.region,
            "timezone": new_region.timezone,
            "language": new_region.language
        }
        
        return {
            "status_code": 201,
            "message": "Region created successfully",
            "data": response_data
        }
    

    def fetch_all(self, db: Session, **query_params: Optional[Any]) -> Dict[str, Any]:
        '''Fetch all Region with option to search using query parameters'''

        query = db.query(LanguageRegionTimezoneSetting)

        # Enable filter by query parameter
        if query_params:
            for column, value in query_params.items():
                if hasattr(LanguageRegionTimezoneSetting, column) and value:
                    query = query.filter(getattr(LanguageRegionTimezoneSetting, column).ilike(f'%{value}%'))

        regions = query.all()

        # Prepare the response data
        response_data = [
            {
                "region": region.region,
                "timezone": region.timezone,
                "language": region.language
            } for region in regions
        ]

        return {
            "status_code": 200,
            "message": "Regions retrieved successfully",
            "data": response_data
        }
    

    def fetch(self, db: Session, region_id: str) -> Dict[str, Any]:
        '''Fetches a Region by id'''

        region = check_model_existence(db, LanguageRegionTimezoneSetting, region_id)

        response_data = {
            "region": region.region,
            "timezone": region.timezone,
            "language": region.language
        }

        return {
            "status_code": 200,
            "message": "Region retrieved successfully",
            "data": response_data
        }
    

    def update(self, db: Session, region_id: str, schema: RegionUpdate) -> Dict[str, Any]:
        '''Updates a Region'''

        region = self.fetch(db=db, region_id=region_id)
        
        # Update the fields with the provided schema data
        update_data = schema.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(region, key, value)
        
        db.commit()
        db.refresh(region)

        response_data = {
            "region": region.region,
            "timezone": region.timezone,
            "language": region.language
        }

        return {
            "status_code": 200,
            "message": "Region updated successfully",
            "data": response_data
        }
    

    def delete(self, db: Session, region_id: str) -> Dict[str, Any]:
        '''Deletes a region service'''
        
        region = self.fetch(db=db, region_id=region_id)
        db.delete(region)
        db.commit()

        return {
            "status_code": 204,
            "message": "Region deleted successfully",
            "data": None
        }

region_service = RegionService()