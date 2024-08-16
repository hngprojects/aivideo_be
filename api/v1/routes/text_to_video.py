from typing import Annotated
from fastapi import APIRouter, status, Depends, Query
from fastapi.security import OAuth2
from sqlalchemy.orm import Session


from api.v1.schemas.text_to_video import (TextInputResponse,
                                          TextInput,
                                          VideoStatusResponse,
                                          VideoPatchRequest)
from api.v1.services.user import user_service, oauth2_scheme
from api.db.database import get_db
from api.v1.services.text_to_video import text_to_video_service

text_to_videos = APIRouter(prefix='/text-to-videos', tags=['TEXT-TO-VIDEO'])


@text_to_videos.post('', status_code=status.HTTP_200_OK,
                    response_model=TextInputResponse)
async def text_to_video_generate(request_text: TextInput,
                     token: Annotated[OAuth2, Depends(oauth2_scheme)],
                     db: Annotated[Session, Depends(get_db)]):
    """
    Generates a video using text input.
        Args:
            request_text: The text from request body
            token: access token for authorization
            db: Database session object
        Returns:
            TextInputResponse: response feedback with video task_id
        Raises:
            HTTPException: If anything goes wrong
    """
    user = user_service.get_current_user(token, db)
    response = await text_to_video_service.create(request_text, user, db)
   
    return response

@text_to_videos.get('/status', status_code=status.HTTP_200_OK,
                   response_model=VideoStatusResponse)
async def get_video_status(token: Annotated[OAuth2, Depends(oauth2_scheme)],
                            db: Annotated[Session, Depends(get_db)],
                            task_id: str = Query(min_length=16)):
    """
    Check the status of a video generation task.
        Args:
            task_id: The id of the task(from query params)
            token: access token for authorization
            db: Database session object
        Returns:
            TextInputResponse: response feedback with video_url(if available)
        Raises:
            HTTPException: If anything goes wrong
    """
    user = user_service.get_current_user(token, db)
    response = await text_to_video_service.fetch(task_id, user, db)
    return response

@text_to_videos.patch('', status_code=status.HTTP_200_OK,
                    response_model=TextInputResponse)
async def text_to_video_update(request_text: VideoPatchRequest,
                     token: Annotated[OAuth2, Depends(oauth2_scheme)],
                     db: Annotated[Session, Depends(get_db)]):
    """
    Update a video.
        Args:
            request_text: The text from request body
            token: access token for authorization
            db: Database session object
        Returns:
            TextInputResponse: response feedback with video_url
        Raises:
            HTTPException: If anything goes wrong
    """
    user = user_service.get_current_user(token, db)
    response = await text_to_video_service.update(request_text, user, db)
   
    return response
