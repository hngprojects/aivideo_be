from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from api.utils.success_response import success_response
from api.db.database import get_db
from api.v1.services.presets import preset_service


preset_router = APIRouter(prefix='/presets', tags=['Presets'])

@preset_router.get('/avatars')
def get_all_avatars(db: Session = Depends(get_db)):
    '''Endpoint to get all avatars'''

    avatars = preset_service.fetch_all_avatars(db=db)

    return success_response(
        status_code=200,
        message='Avatars retrieved successfully',
        data=jsonable_encoder(avatars)
    )


@preset_router.get('/audio')
def get_all_audio(db: Session = Depends(get_db)):
    '''Endpoint to get all audio'''

    audio = preset_service.fetch_all_background_music(db=db)

    return success_response(
        status_code=200,
        message='Audio retrieved successfully',
        data=jsonable_encoder(audio)
    )
    

@preset_router.get('/bg-images')
def get_all_bg_images(db: Session = Depends(get_db)):
    '''Endpoint to get all bg images'''

    bg_images = preset_service.fetch_all_background_images(db=db)

    return success_response(
        status_code=200,
        message='bg-images retrieved successfully',
        data=jsonable_encoder(bg_images)
    )


@preset_router.get('/voices')
def get_all_voices(db: Session = Depends(get_db)):
    '''Endpoint to get all voices'''

    voices = preset_service.fetch_all_voices(db=db)

    return success_response(
        status_code=200,
        message='Voices retrieved successfully',
        data=jsonable_encoder(voices)
    )


@preset_router.get('/load-presets')
def load_all_presets(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    '''Endpoint to load all presets into the db'''
    
    background_tasks.add_task(
        preset_service.load_avatars_in_db,
        db=db
    )
    
    background_tasks.add_task(
        preset_service.load_background_images_in_db,
        db=db
    )
    
    background_tasks.add_task(
        preset_service.load_music_in_db,
        db=db
    )

    return success_response(
        status_code=200,
        message='Presets loading in the background',
    )


@preset_router.delete('/delete-presets', status_code=204)
def delete_all_presets(db: Session = Depends(get_db)):
    '''Endpoint to delete all preset avatars'''

    preset_service.delete_all_avatars(db=db)
    preset_service.delete_all_voices(db=db)
    preset_service.delete_all_music(db=db)
    preset_service.delete_all_background_images(db=db)


@preset_router.get('/avatars/generate', status_code=200)
def generate_new_avatars(background_tasks: BackgroundTasks,db: Session = Depends(get_db)):
    '''Endpoint to generate new avatars'''

    background_tasks.add_task(
        preset_service.generate_avatars,
        db=db
    )

    return success_response(
        status_code=200,
        message='Generating avatar',
    )
    


# @preset_router.get('/load-audio')
# def load_all_audio(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
#     '''Endpoint to get all audio'''

#     background_tasks.add_task(
#         preset_service.load_music_in_db,
#         db=db
#     )

#     return success_response(
#         status_code=200,
#         message='Audio loading in the background',
#     )


# @preset_router.delete('/audio', status_code=204)
# def delete_all_audio(db: Session = Depends(get_db)):
#     '''Endpoint to delete all preset audio'''

#     preset_service.delete_all_music(db=db)

