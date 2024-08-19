import os
from pathlib import Path
import random
from typing import List
from uuid import uuid4
import openai
from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip
import requests

from api.utils.files import delete_file
from api.utils.settings import settings

BASE_DIR = Path(__file__).resolve().parent

class TextToVideoService:

    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

    
    def download_file(self, url, save_path):
        try:
            with requests.get(url, stream=True) as response:
                response.raise_for_status()
                with open(save_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
            print(f"Large file downloaded successfully and saved as {save_path}")

            return save_path
        except requests.RequestException as e:
            print(f"Error downloading large file: {e}")


    def generate_audio_from_script(self, script, voice_over='man'):
        file_path = os.path.join(BASE_DIR, f'audio-{str(uuid4())}.wav')

        female = ["nova", "shimmer"]
        neutral = ["fable", "alloy"]
        male = ["echo", "onyx"]

        voice = male[random.randint(0, 1)]

        if voice_over == 'woman':
            voice = female[random.randint(0, 1)]
        elif voice_over == 'neutral':
            voice = neutral[random.randint(0, 1)]

        response = self.client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=script,
            response_format="wav"
        )

        response.stream_to_file(file_path)
        return file_path
    

    def generate_scene_descriptions(self, script: str):

        response = self.client.completions.create(
            model="gpt-3.5-turbo-instruct",
            prompt=f"Generate five simple scene descriptions that can be used as an image description for the following script:\n\n{script}\n\nScene Descriptions:",
            max_tokens=500
        )
        scenes = response.choices[0].text.strip().split('\n')
        print(scenes)
        return scenes
    

    def generate_images_for_scenes(self, scenes: List):
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

            image_path = self.download_file(
                url=image_url, 
                save_path=os.path.join(BASE_DIR, f"ttvimage-{i:03d}.png")
            )
            images.append(image_path)
        
        return images


    def create_video_with_audio(self, images, audio_file):
        clips = []
        duration_per_image = 10  # Duration each image will be displayed (in seconds)
        transition_duration = 2  # Duration of the fade transition (in seconds)

        video_dir = os.path.join('media', 'downloads', 'video')
        os.makedirs(video_dir, exist_ok=True)
        output_video_file = os.path.join(video_dir, f'ttvideo-{str(uuid4())}.mp4')

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
        video.write_videofile(output_video_file, codec="libx264", audio_codec="aac", fps=24, threads=4)

        return output_video_file

                  
    def process_script(self, script: str):
        audio_file = self.generate_audio_from_script(script)
        scenes = self.generate_scene_descriptions(script)
        images = self.generate_images_for_scenes(scenes)
        save_file = self.create_video_with_audio(images, audio_file)

        delete_file(audio_file)
        for img in images:
            delete_file(img)
        
        save_url = f'{settings.APP_URL}/{save_file}'
        data = {
            "url": save_url,
            "scenes": scenes,
            # "images": images,
            # "scene_image": dict(zip(scenes, images))
        }

        print(data)
        return data


ttv_service = TextToVideoService()
