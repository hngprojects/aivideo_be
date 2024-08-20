import os
from pathlib import Path
from typing import Optional
import wave
from uuid import uuid4
from api.utils.settings import settings
import json
import os
import random
from openai import OpenAI
import requests
import ffmpeg

from api.utils.files import delete_file

BASE_DIR = Path(__file__).resolve().parent

class TalkingAvatarService:
	def download_large_file(self, url, save_path):
		try:
			with requests.get(url, stream=True) as response:
				response.raise_for_status()
				with open(save_path, "wb") as f:
					for chunk in response.iter_content(chunk_size=8192):
						f.write(chunk)
			print(f"Large file downloaded successfully and saved as {save_path}")
		except requests.RequestException as e:
			print(f"Error downloading large file: {e}")
	
	def generate_audio(self, script, voice_over='man'):
		file_path = os.path.join(BASE_DIR, f'audio-{str(uuid4())}.wav')

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

		response.stream_to_file(file_path)
		return file_path
		
	def get_audio_duration(self, audio_path):
		with wave.open(audio_path, "rb") as audio_file:
			num_frames = audio_file.getnframes()
			frame_rate = audio_file.getframerate()
			duration_seconds = num_frames / frame_rate
			return int(duration_seconds)
		
	def set_aspect_ratio(self, aspect_ratio: str):
		if aspect_ratio == 'square':
			return (1000, 1000)
		elif aspect_ratio == 'horizontal':
			return (1920, 1080)
		elif aspect_ratio =='vertical':
			return (720, 1280)
	
	def change_aspect_ratio(self, input_file, output_file, aspect_ratio):
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

		except ffmpeg.Error as e:
			print(f"Error occurred: {e}")


	def process_script(
		self, 
		image_file: str, 
		aspect_ratio: str, 
		script: str, 
		voice_over: str, 
		audio_file: Optional[str]=None
	):
		"""This is to precess the whole talking avatar script

		Args:
			image_file (str): Path to image file
			aspect_ratio (str): Can be one of square, horizontal, vertical
			script (str): Script to be converted to audio
			voice_over (str): Either one of man, woman or neutral
			audio_file Optional{str}: Path to audio file
		Returns:
			str: A string json for the save url and the source of the video
		"""

		audio = self.generate_audio(script=script, voice_over=voice_over)
		files = [
			("input_face", open(image_file, "rb")),
			("input_audio", open(audio, "rb")),
		]
		payload = {
			"functions": None,
			"variables": None,
			"face_padding_top": 0,
			"face_padding_bottom": 18,
			"face_padding_left": 0,
			"face_padding_right": 0,
			"sadtalker_settings": None,
			"selected_model": "Wav2Lip",
		}
		response = requests.post(
			"https://api.gooey.ai/v2/Lipsync/form/",
			headers={
				"Authorization": "Bearer " + settings.GOOEY_API_KEY,
			},
			files=files,
			data={"json": json.dumps(payload)},
		)

		result = response.json()
		print(result)
		url = result['output']['output_video']

		video_dir = os.path.join('media', 'downloads', 'video')
		os.makedirs(video_dir, exist_ok=True)

		# Download video file to the current directory
		initial_save_path = os.path.join(BASE_DIR, f'video-{str(uuid4())}.mp4')
		self.download_large_file(url, initial_save_path)

		if audio_file:
			video_audio_path = os.path.join(BASE_DIR, f'video-{str(uuid4())}.mp4')
			# Add background audio to the file
			self.add_background_audio(
				video_path=initial_save_path,
				audio_path=audio_file,
				output_path=video_audio_path,
			)

		final_save_path = os.path.join(video_dir, f'video-{str(uuid4())}.mp4')
		# Perform aspect ratio resizing based on user input
		self.change_aspect_ratio(
			input_file=video_audio_path if audio_file else initial_save_path,
			output_file=final_save_path,
			aspect_ratio=aspect_ratio
		)

		# Delete the temporary audio and video file after processing is done
		if audio_file:
			delete_file(video_audio_path)
		delete_file(initial_save_path)
		delete_file(audio)

		save_url = f'{settings.APP_URL}/{final_save_path}'
		return {
			'app_url': save_url,
			'source': url
		}


talking_avatar_service = TalkingAvatarService()
