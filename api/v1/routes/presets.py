from fastapi import APIRouter, Request, BackgroundTasks, Depends
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from api.utils.success_response import success_response
from api.db.database import get_db
from api.v1.services.presets import preset_service
from scripts.presets import load_avatars_in_db


preset_router = APIRouter(prefix='/presets', tags=['Presets'])

@preset_router.get("/load-avatars")
def load_avatars_into_db(request: Request, background_tasks: BackgroundTasks):
    '''Endpoint to load avatars into the database'''

    background_tasks.add_task(load_avatars_in_db, request)

    return success_response(
        status_code=200,
        message='Avatars loading in the background'
    )

@preset_router.get('/avatars')
def get_all_avatars(db: Session = Depends(get_db)):
    '''Endpoint to get all avatars'''

    avatars = preset_service.fetch_all_avatars(db=db)

    return success_response(
        status_code=200,
        message='Avatars retrieved successfully',
        data=jsonable_encoder(avatars)
    )
