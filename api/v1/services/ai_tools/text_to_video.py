import os
from pathlib import Path
import random
from typing import List
from uuid import uuid4
import openai
import ffmpeg
from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip, TextClip, CompositeVideoClip
from moviepy.video.tools.subtitles import SubtitlesClip
import requests

from deepgram_captions import DeepgramConverter, srt
from deepgram import (
    DeepgramClient,
    PrerecordedOptions,
    FileSource,
)

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
    

    def generate_subtitles_from_audio(self, audio_file: str):
        try:
            deepgram = DeepgramClient(settings.DEEPGRAM_API_KEY)

            with open(audio_file, "rb") as file:
                buffer_data = file.read()

            payload: FileSource = {
                "buffer": buffer_data,
            }

            options = PrerecordedOptions(
                model="nova-2",
                smart_format=True,
            )

            response = deepgram.listen.prerecorded.v("1").transcribe_file(payload, options)

            transcription = DeepgramConverter(dg_response=response)
            captions = srt(transcription)

            subtitles_file = os.path.join(BASE_DIR, f'subtitles-{uuid4()}.srt')
            with open(subtitles_file, 'w') as subtitles:
                subtitles.write(captions)
            
            return subtitles_file

        except Exception as e:
            print(f"Exception: {e}")


    def create_video_with_images(self, images: List[str], audio_file: str):
        clips = []
        duration_per_image = 10  # Duration each image will be displayed (in seconds)
        transition_duration = 2  # Duration of the fade transition (in seconds)

        output_video_file = os.path.join(BASE_DIR, f'ttvideo-{str(uuid4())}.mp4')

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
    
    def add_subtitles_to_video(self, input_video: str, subtitles_file: str, output_video: str):
        # Load the input video
        input_stream = ffmpeg.input(input_video)
        
        # Apply the subtitles filter
        video = input_stream.video.filter('subtitles', subtitles_file)
        
        # Combine the video with audio (if any) and output the result
        output = ffmpeg.output(video, input_stream.audio, output_video)
        
        # Run the command
        ffmpeg.run(output)

        return output_video
    

    def set_aspect_ratio(self, aspect_ratio: str):
        if aspect_ratio == 'square':
            return (1000, 1000)
        elif aspect_ratio == 'horizontal':
            return (1920, 1080)
        elif aspect_ratio =='vertical':
            return (720, 1280)
        

    def change_aspect_ratio(self, input_file: str, output_file: str, aspect_ratio: str):
        """
        Change the aspect ratio of a video by resizing and/or adding padding.
        
        :param input_file: Path to the input video file.
        :param output_file: Path to save the output video file.
        :param aspect_ratio: Desired aspect ratio of the video, Can be one of square, horizontal or veritcal.
        """

        aspect_ratio = self.set_aspect_ratio(aspect_ratio)
        # Define the scaling and padding filter
        filter_complex = (
            f"scale={aspect_ratio[0]}:{aspect_ratio[1]}:force_original_aspect_ratio=decrease,"
            f"pad={aspect_ratio[0]}:{aspect_ratio[1]}:(ow-iw)/2:(oh-ih)/2"
        )

        try:
            # Run the ffmpeg command
            ffmpeg.input(input_file).output(output_file, vf=filter_complex).run(overwrite_output=True)
            print(f"Aspect ratio changed. Output saved to {output_file}")

            return output_file
        
        except ffmpeg.Error as e:
            print(f"An error occurred: {e}")


    def add_background_audio(self, video_path: str, audio_path: str, output_path: str):
        try:
            # Load the video file with its audio
            video = ffmpeg.input(video_path)

            # Load the background audio and adjust its volume
            background_audio = ffmpeg.input(audio_path).filter('volume', 0.2)

            # Adjust the volume of the original audio from the video
            original_audio = video.audio.filter('volume', 1.0)

            # Combine the original audio with the background audio
            combined_audio = ffmpeg.filter_([original_audio, background_audio], 'amix', inputs=2)

            # Combine the video with the combined audio
            output = ffmpeg.output(
                video.video,                  # Video stream
                combined_audio,               # Combined audio stream
                output_path,                  # Output file path
                vcodec='copy',                # Copy the video codec (no re-encoding)
                acodec='aac',                 # Encode the audio with AAC codec
                strict='experimental',        # Allow use of experimental codecs
                shortest=None                 # Stop the output when the shortest input ends
            )

            # Run the ffmpeg command
            ffmpeg.run(output, overwrite_output=True)

            print(f"Successfully added background audio to {output_path}")

            return output_path

        except ffmpeg.Error as e:
            print(f"Error occurred: {e}")

                  
    # def process_script(self, script: str, voice_over: str, background_audio: str, aspect_ratio: str):
    def process_script(
        self, 
        script: str, 
        scenes: List[str], 
        voice_over: str, 
        background_audio: str, 
        aspect_ratio: str
    ):

        audio_file = self.generate_audio_from_script(script, voice_over)
        subtitle_file = self.generate_subtitles_from_audio(audio_file)
        # scenes = self.generate_scene_descriptions(script)
        images = self.generate_images_for_scenes(scenes)
        video_file = self.create_video_with_images(images, audio_file)
        
        # Add subtitles to video
        video_with_subtitles_path = os.path.join(BASE_DIR, f'ttvideo-{str(uuid4())}.mp4')
        video_with_subtitles = self.add_subtitles_to_video(
            input_video=video_file, 
            subtitles_file=subtitle_file, 
            output_video=video_with_subtitles_path
        )

        # Add background music to video
        video_with_bg_music_path = os.path.join(BASE_DIR, f'ttvideo-{str(uuid4())}.mp4')
        video_with_audio = self.add_background_audio(
            video_path=video_with_subtitles, 
            audio_path=background_audio, 
            output_path=video_with_bg_music_path
        )

        # Set up for final result
        video_dir = os.path.join('media', 'downloads', 'video')
        os.makedirs(video_dir, exist_ok=True)
        output_video_file = os.path.join(video_dir, f'ttvideo-{str(uuid4())}.mp4')
        # Adjust aspect ratio
        final_result_file = self.change_aspect_ratio(
            input_file=video_with_audio, 
            output_file=output_video_file, 
            aspect_ratio=aspect_ratio
        )

        # Delete unnecessary files
        delete_file(audio_file)
        delete_file(subtitle_file)
        delete_file(video_file)
        delete_file(video_with_subtitles_path)
        delete_file(video_with_bg_music_path)
        for img in images:
            delete_file(img)
        
        save_url = f'{settings.APP_URL}/{final_result_file}'
        data = {
            "url": save_url
        }

        print(data)
        return data


ttv_service = TextToVideoService()
