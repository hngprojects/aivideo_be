from typing import Annotated
from fastapi import status, Depends, HTTPException
from sqlalchemy.orm import Session


from api.v1.schemas.text_to_video import (TextInputResponse,
                                          TextInput,
                                          TextInputData,
                                          VideoTask,
                                          VideoStatusResponse,
                                          VideoPatchRequest)
from api.db.database import get_db
from api.core.base.async_services import AsyncService
from api.v1.models import User, TextToVideo
from api.core.dependencies.celery.tasks.video_tasks import (create_video_from_text_task)


class TextToVideoService(AsyncService):
    """
    Class service for text-to-video
    """
    async def create(self, request_text: TextInput,
                     user: User,
                     db: Annotated[Session, Depends(get_db)]):
        """
        Creates a video from texts.


        Args:
            request_text:
        """
        # trigger celery task
        job_id =  create_video_from_text_task.delay(request_text.text, user.id)

        # Save task_id and status to database
        video_task = TextToVideo(
            user_id=user.id,
            job_id=str(job_id)
        )
        db.add(video_task)
        db.commit()
        # return TextInputResponse()
        return TextInputResponse(
            message='video is currently been processed',
            status_code=status.HTTP_200_OK,
            data=TextInputData(
                task_id=str(job_id),
                status='Task is in queue'
            )
        )


    async def fetch(self, task_id: str,
                     user: User,
                     db: Annotated[Session, Depends(get_db)]):
        """
        Fetch
        """
        task = db.query(TextToVideo).filter_by(
            job_id=task_id,
            user_id=user.id
        ).first()
        if task:
            data =  VideoTask(
                    status=task.status,
                    task_id=task_id,
                    user_id=user.id,
                    video_url=task.video_url
                )
        else:
            data =  VideoTask(
                    status='Task is in queue',
                    task_id=task_id,
                    user_id=user.id,
                )
        return VideoStatusResponse(
                message='successful',
                status_code=status.HTTP_200_OK,
                data=data
            )
   
    async def update(self, patch_request: VideoPatchRequest,
                     user: User,
                     db: Annotated[Session, Depends(get_db)]):
        """
        Update
        """
        return TextInputResponse(
            message='successful',
            status_code=200,
            data=TextInputData(
                task_id=patch_request.task_id
            )
        )
   
    async def fetch_all(self, request_text: TextInput,
                     user: User,
                     db: Annotated[Session, Depends(get_db)]):
        """
        Fetch_all
        """
        pass
   
    async def delete(self, request_text: TextInput,
                     user: User,
                     db: Annotated[Session, Depends(get_db)]):
        """
        Delete
        """
        pass

text_to_video_service = TextToVideoService()
