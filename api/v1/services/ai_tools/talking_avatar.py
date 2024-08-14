import os
import wave
from PIL import Image, ImageEnhance
import imageio
import numpy as np
from uuid import uuid4
from api.utils.settings import settings
import json
import os
from unrealspeech import UnrealSpeechAPI, save
import requests



class TalkingAvatarService:
	
	def generate_audio(self, script, male=False):
		file_path = os.path.join('media', 'output', f'{str(uuid4())}.mp4')
		speech_api = UnrealSpeechAPI(settings.UNREAL_SPEECH_API_KEY)
		text_to_speech = script
		timestamp_type = "sentence"
		voice_id = "Will" if male else "Scarlett"
		bitrate = "192k"
		speed = 0 
		pitch = 1.0
		audio_data = speech_api.speech(text=text_to_speech,voice_id=voice_id, bitrate=bitrate, timestamp_type=timestamp_type, speed=speed, pitch=pitch)
		save(audio_data, file_path)
		return file_path
		
	def get_audio_duration(self, audio_path):
		with wave.open(audio_path, "rb") as audio_file:
			num_frames = audio_file.getnframes()
			frame_rate = audio_file.getframerate()
			duration_seconds = num_frames / frame_rate
			return duration_seconds

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

	def process_script(self, input, image_type, script="Hello i'm the real slim shady baby.",fps=3):
		audio = self.generate_audio(script)
		seconds = self.get_audio_duration(audio)
		total_frames = seconds * fps

		im = self.open_and_resize_image(input, image_type)

		color_percentage_for_each_frame = 1.0

		write_to = os.path.join('media', 'output', 'video', f'{str(uuid4())}.mp4')

		writer = imageio.get_writer(write_to, format='mp4', mode='I', fps=fps)

		for i in range(total_frames):
			processed = ImageEnhance.Color(im).enhance(color_percentage_for_each_frame)
			writer.append_data(np.asarray(processed))


		writer.close()		

		files = [
			("input_face", open(write_to, "rb")),
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
		return result['output_video']


talking_avatar_service = TalkingAvatarService()