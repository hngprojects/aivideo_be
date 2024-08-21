import os
from typing import Optional
from uuid import uuid4
from api.utils.settings import settings
import json
import os
import openai
import requests

from api.utils.files import delete_file
from api.v1.services.ai_tools.general_video_service import CURRENT_DIRECTORY, video_service


class TalkingAvatarService:

	def __init__(self):
		self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
		

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

		audio = video_service.generate_audio_from_script(script=script, voice_over=voice_over)
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
		initial_save_path = os.path.join(CURRENT_DIRECTORY, f'video-{str(uuid4())}.mp4')
		video_service.download_file(url, initial_save_path)

		if audio_file:
			video_audio_path = os.path.join(CURRENT_DIRECTORY, f'video-{str(uuid4())}.mp4')
			# Add background audio to the file
			video_service.add_background_audio(
				video_path=initial_save_path,
				audio_path=audio_file,
				output_path=video_audio_path,
			)

		final_save_path = os.path.join(video_dir, f'video-{str(uuid4())}.mp4')

		# Perform aspect ratio resizing based on user input
		video_service.change_aspect_ratio(
			input_file=video_audio_path if audio_file else initial_save_path,
			output_file=final_save_path,
			aspect_ratio=aspect_ratio
		)

		# Delete the temporary audio and video file after processing is done
		if audio_file:
			delete_file(video_audio_path)
		delete_file(initial_save_path)
		delete_file(audio)

		# Compress video
		final_save_path = self.compress_video(input_file=final_save_path, bitrate=500) 
		
		save_url = f'{settings.APP_URL}/{final_save_path}'
		return {
			'app_url': save_url,
			'source': url
		}


talking_avatar_service = TalkingAvatarService()
