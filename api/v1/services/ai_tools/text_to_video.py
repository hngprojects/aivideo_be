import os
from pathlib import Path
import random
from typing import List, Optional
from uuid import uuid4
import openai
import ffmpeg
from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip
import requests

from deepgram_captions import DeepgramConverter, srt
from deepgram import (
    DeepgramClient,
    PrerecordedOptions,
    FileSource,
)

from api.utils.minio_service import minio_service
from api.utils import mime_types
from api.utils.files import delete_file
from api.utils.settings import settings
from api.v1.services.ai_tools.general_video_service import video_service


class TextToVideoService:

    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    

    def generate_scene_descriptions(self, script: str):

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"Generate five simple scene descriptions that can be used as an image description for the following script and I do not want any form of numbering or bulleting on them. Also, don not say anoy other thing other than the scene descriptions. Here is the script: :\n\n{script}\n\nScene Descriptions:"}
            ]
        )
        # scenes = response.choices[0].message.content.strip().split('\n')
        scenes = [scene.strip() for scene in response.choices[0].message.content.strip().split('\n') if scene.strip()]
        return scenes
    

    def recompose_script(self, script: str):

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"I will add a script for you to recompose. Do not say anything else than the recomposition:\n\n{script}"}
            ]
        )
        recomposed_script = response.choices[0].message.content
        return recomposed_script
    

    def generate_images_for_scenes(self, scenes: List[str]):
        images = []

        for i, scene in enumerate(scenes):
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=f"Generate an image for this scene or related: {scene}",
                size="1024x1024",
                quality="standard",
                n=1,
            )

            image_url = response.data[0].url

            image_path = video_service.download_file(
                url=image_url, 
                save_path=os.path.join(settings.TEMP_DIR, f"ttvimage-{i:03d}.png")
            )
            images.append(image_path)
        
        return images


    def create_video_with_images(self, images: List[str], audio_file: str):
        clips = []
        duration_per_image = 10  # Duration each image will be displayed (in seconds)
        transition_duration = 2  # Duration of the fade transition (in seconds)

        output_video_file = os.path.join(settings.TEMP_DIR, f'ttvideo-{str(uuid4())}.mp4')

        for image_file in images:
            # Create an ImageClip for each image
            img_clip = ImageClip(image_file).set_duration(duration_per_image)
            
            # Apply fade in and fade out effects to create transitions
            clip = img_clip.fadein(transition_duration).fadeout(transition_duration)
            clips.append(clip)

        # Concatenate the clips with transition effects
        video = concatenate_videoclips(clips, method="compose")

        # Add the audio file
        audio = AudioFileClip(audio_file)
        video = video.set_audio(audio)

        # Set the duration of the video to match the audio duration
        video = video.set_duration(audio.duration)

        # Write the final video file to the specified output path
        video.write_videofile(output_video_file, codec='libx264', audio_codec="aac", fps=24, threads=4)

        return output_video_file
    
    
    def process_script(
        self, 
        script: str, 
        scenes: List[str], 
        voice_over: str, 
        aspect_ratio: str,
        background_audio: Optional[str] = None, 
    ):

        audio_file = video_service.generate_audio_from_script(script, voice_over)
        subtitle_file = video_service.generate_subtitles_from_audio(audio_file)
        # scenes = self.generate_scene_descriptions(script)
        images = self.generate_images_for_scenes(scenes)
        video_file = self.create_video_with_images(images, audio_file)
        
        # Add subtitles to video
        video_with_subtitles_path = os.path.join(settings.TEMP_DIR, f'ttvideo-{str(uuid4())}.mp4')
        video_with_subtitles = video_service.add_subtitles_to_video(
            input_video=video_file, 
            subtitles_file=subtitle_file, 
            output_video=video_with_subtitles_path
        )

        if background_audio:
            # Add background music to video
            video_with_bg_music_path = os.path.join(settings.TEMP_DIR, f'ttvideo-{str(uuid4())}.mp4')
            video_with_audio = video_service.add_background_audio(
                video_path=video_with_subtitles, 
                audio_path=background_audio, 
                output_path=video_with_bg_music_path
            )

        # Set up for final result
        video_dir = os.path.join(settings.STORAGE_DIR, 'video')
        os.makedirs(video_dir, exist_ok=True)
        output_video_file = os.path.join(video_dir, f'ttvideo-{str(uuid4())}.mp4')
        # Adjust aspect ratio
        final_result_file = video_service.change_aspect_ratio(
            input_file=video_with_audio if background_audio is not None else video_with_subtitles, 
            output_file=output_video_file, 
            aspect_ratio=aspect_ratio
        )

        # Delete unnecessary files
        delete_file(audio_file)
        delete_file(subtitle_file)
        delete_file(video_file)
        delete_file(video_with_subtitles_path)
        if background_audio:
            delete_file(video_with_bg_music_path)
        for img in images:
            delete_file(img)
        
        # save_url = f'{settings.APP_URL}/{final_result_file}'

        minio_save_file = f'ttvid-{str(uuid4())}.mp4'
        save_url, download_url = minio_service.upload_to_minio(
            bucket_name='text-to-video',
            source_file=final_result_file,
            destination_file=minio_save_file,
            content_type=mime_types.VIDEO_MP4
        )

        data = {
            "url": save_url,
            "download_url": download_url,
        }

        delete_file(final_result_file)
        return data


ttv_service = TextToVideoService()
