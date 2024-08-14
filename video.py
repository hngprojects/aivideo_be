import requests 
import os
from api.utils.settings import settings
import json
from uuid import uuid4



def download_large_file(url, save_path):
		try:
			with requests.get(url, stream=True) as response:
				response.raise_for_status()
				with open(save_path, "wb") as f:
					for chunk in response.iter_content(chunk_size=8192):
						f.write(chunk)
			print(f"Large file downloaded successfully and saved as {save_path}")
		except requests.RequestException as e:
			print(f"Error downloading large file: {e}")

files = [
			("input_face", open("media/uploads/user_avatars/mark-essien-e1580122566517-1f1faf6b54.jpg", "rb")),
			("input_audio", open("media/output/d8b6d28e-ff7f-4e6a-95b7-9c147eebefc7.wav", "rb")),
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
print(response.status_code, response.content)
result = response.json()
url = result['output']['output_video']
save_path = os.path.join('media', 'output', 'video', f'{str(uuid4())}.mp4')
download_large_file(url, save_path)


