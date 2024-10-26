import os
from typing import Optional
from uuid import uuid4
from api.utils import mime_types
from api.utils.minio_service import minio_service
from api.utils.settings import settings
import json
import os
import openai
import requests

from api.utils.files import delete_file
from api.v1.services.tools.general_video_service import video_service


class TalkingAvatarService:

	def __init__(self):
		self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

	
	def generate_talking_avatar_video(self, image_file, audio):
		files = [
			("input_face", open(image_file, "rb")),
			("input_audio", open(audio, "rb")),
		]
		payload = {
			"functions": None,
			"variables": {},
			"face_padding_top": 0,
			"face_padding_bottom": 18,
			"face_padding_left": 0,
			"face_padding_right": 0,
			"sadtalker_settings": {
				"still": True,
				"ref_pose": None,
				"input_yaw": None,
				"input_roll": None,
				"pose_style": 0,
				"preprocess": "resize",
				"input_pitch": None,
				"ref_eyeblink": None,
				"expression_scale": 1,
			},
			"selected_model": "SadTalker",
		}

		print('Making API request to get talking avatar...')
		response = requests.post(
			"https://api.gooey.ai/v2/Lipsync/form/",
			headers={
				"Authorization": "Bearer " + settings.GOOEY_API_KEY,
			},
			files=files,
			data={"json": json.dumps(payload)},
		)

		result = response.json()
		url = result['output']['output_video']

		return url
		

talking_avatar_service = TalkingAvatarService()
