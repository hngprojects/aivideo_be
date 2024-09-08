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
from api.v1.services.ai_tools.general_video_service import video_service


class TalkingAvatarService:

	def __init__(self):
		self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
		

	def process_script(
		self, 
		image_file: str, 
		aspect_ratio: str, 
		script: str, 
		voice_over: str, 
		audio_file: Optional[str]=None,
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

		print('Generating audio from script...')
		audio = video_service.generate_audio_from_script(script=script, voice_over=voice_over)
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

		print('Downloading generated video...')
		video_dir = os.path.join(settings.STORAGE_DIR, 'video')
		os.makedirs(video_dir, exist_ok=True)

		# Download video file to the current directory
		initial_save_path = os.path.join(settings.TEMP_DIR, f'video-{str(uuid4())}.mp4')
		video_service.download_file(url, initial_save_path)

		if audio_file:
			print('Adding background music...')
			video_audio_path = os.path.join(settings.TEMP_DIR, f'video-{str(uuid4())}.mp4')
			# Add background audio to the file
			video_service.add_background_audio(
				video_path=initial_save_path,
				audio_path=audio_file,
				output_path=video_audio_path,
			)

		video_dir = os.path.join(settings.STORAGE_DIR, 'video')
		os.makedirs(video_dir, exist_ok=True)
		final_save_path = os.path.join(video_dir, f'video-{str(uuid4())}.mp4')

		print('Changing aspect ratio...')
		# Perform aspect ratio resizing based on user input
		video_service.change_aspect_ratio(
			input_file=video_audio_path if audio_file else initial_save_path,
			output_file=final_save_path,
			aspect_ratio=aspect_ratio
		)

		print('Cleaning up...')
		# Delete the temporary audio and video file after processing is done
		if audio_file:
			delete_file(video_audio_path)
		delete_file(initial_save_path)
		delete_file(audio)

		print('Generating video preview and download links...')
		minio_save_file = f'tavtr-{str(uuid4())}.mp4'
		save_url, download_url = minio_service.upload_to_minio(
			bucket_name='talking-avatar',
			source_file=final_save_path,
			destination_file=minio_save_file,
			content_type=mime_types.VIDEO_MP4
		)

		# Compress video and save to minio as well
		low_quality = video_service.compress_video(input_file=final_save_path, bitrate=500)
		low_quality_vid_preview, low_quality_vid_download = minio_service.upload_to_minio(
			bucket_name='talking-avatar',
			source_file=low_quality,
			destination_file=f'tavtr-{str(uuid4())}.mp4',
			content_type=mime_types.VIDEO_MP4
		)
		medium_quality = video_service.compress_video(input_file=final_save_path, bitrate=1080)
		medium_quality_vid_preview, medium_quality_vid_download = minio_service.upload_to_minio(
			bucket_name='talking-avatar',
			source_file=medium_quality,
			destination_file=f'tavtr-{str(uuid4())}.mp4',
			content_type=mime_types.VIDEO_MP4
		)

		print('Adding finishing touches')
		delete_file(medium_quality)
		delete_file(low_quality)
		delete_file(final_save_path)
		
		print('Done!!!')
		return {
			'app_url': save_url,
			'source': url,
			'quality': {
				"low_quality": low_quality_vid_download,
				"medium_quality": medium_quality_vid_download,
				"high_quality": download_url,
			}
		}


talking_avatar_service = TalkingAvatarService()
