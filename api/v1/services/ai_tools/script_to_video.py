import os, random, secrets

from typing import List, Optional
from uuid import uuid4
import openai
from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip

from api.utils.minio_service import minio_service
from api.utils import mime_types
from api.utils.files import delete_file
from api.utils.settings import settings
from api.v1.services.ai_tools.general_video_service import video_service


class ScriptToVideoService:

    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        self.openrouter_client = openai.OpenAI(
            base_url='https://openrouter.ai/api/v1',
            api_key=settings.OPENROUTER_API_KEY
        )
    

    def generate_scene_descriptions(self, script: str):

        response = self.openrouter_client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"Generate five simple scene descriptions that can be used as an image description for the following script and I do not want any form of numbering or bulleting on them. Also, don not say anoy other thing other than the scene descriptions. Here is the script: :\n\n{script}\n\nScene Descriptions:"}
            ]
        )
        scenes = [scene.strip() for scene in response.choices[0].message.content.strip().split('\n') if scene.strip()]
        return scenes
    

    def recompose_script(self, script: str):

        response = self.openrouter_client.chat.completions.create(
            model="openai/gpt-4o-mini",
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
    

ttv_service = ScriptToVideoService()
