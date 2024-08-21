import os
from pathlib import Path
import wave
import random
from uuid import uuid4
import openai
import ffmpeg
import requests
from moviepy.editor import VideoFileClip

from deepgram_captions import DeepgramConverter, srt
from deepgram import (
    DeepgramClient,
    PrerecordedOptions,
    FileSource,
)

from api.utils.files import delete_file
from api.utils.settings import settings

CURRENT_DIRECTORY = Path(__file__).resolve().parent

class GeneralVideoService:

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

    
    def get_audio_duration(self, audio_path):
        with wave.open(audio_path, "rb") as audio_file:
            num_frames = audio_file.getnframes()
            frame_rate = audio_file.getframerate()
            duration_seconds = num_frames / frame_rate
            return int(duration_seconds)

    
    def compress_video(self, input_file, bitrate: int=700):
        """
        Compresses a video file using moviepy.

        Parameters:
        - input_file: Path to the input video file.
        - output_file: Path to the output compressed video file.
        - bitrate: Desired bitrate for the output video (e.g., '1000k' for 1000 kbps).
        """

        output_file = os.path.join('media', 'downloads', 'video', f'video-{str(uuid4())}.mp4')
        try:
            clip = VideoFileClip(input_file)
            clip.write_videofile(output_file, bitrate=f"{bitrate}k")
            print(f"Video compressed successfully: {output_file}")
            delete_file(input_file)
            return output_file
        except Exception as e:
            print(f"Error compressing video: {e}")
            return input_file


    def generate_audio_from_script(self, script, voice_over='man'):
        file_path = os.path.join(CURRENT_DIRECTORY, f'audio-{str(uuid4())}.wav')

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

            subtitles_file = os.path.join(CURRENT_DIRECTORY, f'subtitles-{uuid4()}.srt')
            with open(subtitles_file, 'w') as subtitles:
                subtitles.write(captions)
            
            return subtitles_file

        except Exception as e:
            print(f"Exception: {e}")
    
    
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


video_service = GeneralVideoService()
