from typing import Annotated
from fastapi import status, Depends, HTTPException
from sqlalchemy.orm import Session
from pathlib import Path
from uuid import uuid4
import json
import random
from openai import OpenAI
import ffmpeg
from ffmpeg import Error
import httpx

from api.utils.files import delete_file
from api.utils.settings import settings
from api.v1.schemas.text_to_video import (TextInputResponse,
                                          TextInput,
                                          TextInputData,
                                          VideoTask,
                                          VideoStatusResponse,
                                          VideoPatchRequest)
from api.db.database import get_db
from api.core.base.async_services import AsyncService
from api.v1.models import User, TextToVideo
from api.utils.text_to_video import create_video_from_text
from api.v1.services.ai_tools.talking_avatar import talking_avatar_service


BASE_DIR = Path(__file__).resolve().parent


class TextToVideoService(AsyncService):
    """
    Class service for text-to-video
    """
    async def create(self, request_text: TextInput,
                     db: Annotated[Session, Depends(get_db)]):
        """
        Creates a video from texts.

        Args:
            request_text:
        """
        # trigger celery task
        data: dict = await create_video_from_text(request_text.text)

        # Save task_id and status to database
        video_task = TextToVideo(
            job_id=str(data.get('task_id', '')),
            task_id=str(data.get("uuid")),
            status='Task is in queue'
        )
        db.add(video_task)
        db.commit()

        return TextInputResponse(
            message='video is currently been processed',
            status_code=status.HTTP_200_OK,
            data=TextInputData(
                task_id=str(data.get("uuid")),
                status='Task is in queue'
            )
        )

    async def fetch(self, task_id: str,
                     db: Annotated[Session, Depends(get_db)]):
        """
        Fetch
        """
        task = db.query(TextToVideo).filter_by(
            task_id=task_id
        ).first()
        if task:
            data = VideoTask(
                    status=task.status,
                    task_id=task_id,
                    video_url=task.video_url
                )
        else:
            data =  VideoTask(
                    status='Task is in queue',
                    task_id=task_id,
                )
        return VideoStatusResponse(
                message='successful',
                status_code=status.HTTP_200_OK,
                data=data
            )
   
    async def update(self, patch_request: VideoPatchRequest,
                     db: Annotated[Session, Depends(get_db)]):
        """
        Update
        """
        video = db.query(TextToVideo).filter_by(task_id=patch_request.task_id).first()
        if not video:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Task not found")
        # Trigger video editing based on the update request
        video_url = await self.edit_video(patch_request.aspect_ratio,
                              patch_request.text,
                              video.video_url,
                              patch_request.voice_over)
        video.status = 'success'
        db.commit()
        # call video_edit method with courotine
        return TextInputResponse(
            message='successful',
            status_code=200,
            data=TextInputData(
                task_id=patch_request.task_id,
                video_url=video_url
            )
        )
   
    async def edit_video(self, aspect_ratio,
                   script, video_url, voice_over: str):
        """
        Edits a video by adding an audio track and changing the aspect ratio.
        """
        # Generate audio from the script
        if voice_over:
            audio = await self.generate_audio(script=script,
                                        voice_over=voice_over)
        video_dir = BASE_DIR / 'media' / 'downloads' / 'video'

        video_dir.mkdir(parents=True, exist_ok=True)

        # Download and process the video
        initial_save_path = BASE_DIR / f'video-{str(uuid4())}.mp4'
        await talking_avatar_service.download_large_file(video_url,
                                             initial_save_path)

        final_save_path = video_dir / f'video-{str(uuid4())}.mp4'

        # Perform aspect ratio resizing based on user input
        await talking_avatar_service.change_aspect_ratio(
            input_file=initial_save_path,
            output_file=final_save_path,
            aspect_ratio=aspect_ratio
        )

        # Delete the temporary audio and video file after processing is done
        delete_file(initial_save_path)
        if audio:
            delete_file(audio)

        save_url = f'{settings.APP_URL}/{final_save_path.relative_to(BASE_DIR)}'
        return json.dumps({
            'video_url': save_url,
        })
   
    async def mix_video_audio(self,
                              video_path: str,
                              audio_path: str,
                              output_path: str):
        """
        Combine the video with the generated audio.
       
        Args:
           :param video_path: Path to the input video file.
           :param audio_path: Path to the input audio file.
           :param output_path: Path to save the output video with audio.
        """
        video_path = Path(video_path)
        audio_path = Path(audio_path)
        output_path = Path(output_path)
        try:
            (ffmpeg.input(video_path)
             .output(audio_path, output_path, vcodec='copy', acodec='aac')
             .run(overwrite_output=True))
        except Error as exc:
            print('error occured in video editing: ', exc)
            raise exc

    def generate_audio(self, script, voice_over='man'):
        file_path = BASE_DIR / f'audio-{str(uuid4())}.wav'

        female = ["nova", "shimmer"]
        neutral = ["fable", "alloy"]
        male = ["echo", "onyx"]

        voice = male[random.randint(0, 1)]

        if voice_over == 'woman':
            voice = female[random.randint(0, 1)]
        elif voice_over == 'neutral':
            voice = neutral[random.randint(0, 1)]

        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=script,
            response_format="wav"
        )

        # Use httpx to stream the response content to a file
        with httpx.stream("GET", response.url) as stream_response:
            with open(file_path, "wb") as f:
                for chunk in stream_response.iter_bytes(chunk_size=8192):
                    f.write(chunk)


        return str(file_path)

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