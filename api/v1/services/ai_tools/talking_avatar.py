import os
import wave
from PIL import Image
from uuid import uuid4
from api.utils.settings import settings
import json
import os
import random
from openai import OpenAI
import requests



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
	
	def generate_audio(self, script="Today is a wonderful day to build something people love!", male_voice=True):
		file_path = os.path.join('media', 'output', f'{str(uuid4())}.wav')
		female = ["nova", "shimmer"]
		neutral = ["fable", "alloy"]
		male = ["echo", "onyx"]
		voice = male[random.randint(0, 1)]
		if not male_voice:
			voice = female[random.randint(0, 1)]
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

	def open_and_resize_image(self, input, image_type):
		img = Image.open(input)

		if image_type == "square":
			max_size = (1080, 1080)
		elif image_type == "vertical":
			max_size = (1080, 1350)
		elif image_type == "horizontal":
			max_size = (1080, 566)
		else:
			raise ValueError("Invalid image type. Supported types: 'square', 'vertical', 'horizontal'")

		img.thumbnail(max_size)
		return img

	def process_script(self, image_file, image_type, script="Hello i'm the real slim shady baby.",fps=3):
		audio = self.generate_audio(script)
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
		print("got here")
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
		save_path = os.path.join('media', 'output', 'video', f'{str(uuid4())}.mp4')
		self.download_large_file(url, save_path)
		return True



talking_avatar_service = TalkingAvatarService()