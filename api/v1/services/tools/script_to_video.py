import os, random, secrets

from typing import List, Optional
from uuid import uuid4
import openai
from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip

from api.utils.minio_service import minio_service
from api.utils.openai_service import openai_service
from api.utils import mime_types
from api.utils.files import delete_file
from api.utils.settings import settings
from api.v1.services.tools.general_video_service import video_service


class ScriptToVideoService:

    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    
    def generate_scene_descriptions(self, script: str):
        
        response = openai_service.prompt_ai(
            prompt=f'Generate five simple and short scene descriptions not more than 100 characters that can be used as an image description for AI and stock images and videos API query for the following script and I do not want any form of numbering or bulleting on them. Also, do not say any other thing other than the scene descriptions. Here is the script: :\n\n{script}\n\nScene Descriptions:',
            system_role_desc='You are a great scene description generator.'
        )
        
        scenes = [scene.strip() for scene in response.strip().split('\n') if scene.strip()]
        return scenes
    

    def recompose_script(self, script: str):
        
        response = openai_service.prompt_ai(
            prompt=f'I will add a script for you to recompose. Do not say anything else than the recomposition:\n\n{script}',
            system_role_desc='You are a great text recomposer.'
        )
        
        return response
    

    def generate_images_for_scenes(self, scenes: List[str]):
        images = []

        for i, scene in enumerate(scenes):
            # random_suffix = random.randint(1, 10000000)
            random_suffix = secrets.token_hex(6)
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
                save_path=os.path.join(settings.TEMP_DIR, f"ttvimage-{i:03d}-{random_suffix}.png")
            )
            images.append(image_path)
        
        return images


    def create_video_with_images(self, images: List[str], audio_file: str):
        clips = []
        duration_per_image = 10  # Duration each image will be displayed (in seconds)
        transition_duration = 2  # Duration of the fade transition (in seconds)

        output_video_file = os.path.join(settings.TEMP_DIR, f'ttvideo-{str(uuid4().hex)}.mp4')

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
    

ttv_service = ScriptToVideoService()
