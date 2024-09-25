import requests, os, json
from uuid import uuid4

from api.utils.settings import settings


class GeneralService:

    def download_file(self, url: str, extension: str, prefix_file_name: str = 'file'):

        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()  # Check for errors in the response
            
            file_path = os.path.join(settings.TEMP_DIR, f'{prefix_file_name}-{uuid4()}.{extension}')
            with open(file_path, "wb") as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)

            return file_path

        except requests.RequestException as e:
            raise e
        
    
general_service = GeneralService()
