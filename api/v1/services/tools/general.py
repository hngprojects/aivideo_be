import requests, os, json, subprocess
from uuid import uuid4

from api.utils.settings import settings


class GeneralService:

    def download_file(self, url: str, extension: str, prefix_file_name: str = 'file'):
        
        # headers = {
        #     # 'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'
        #     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
        # }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
        }

        try:
            # response = requests.get(url, stream=True, headers=headers)
            response = requests.get(url, stream=True)
            response.raise_for_status()  # Check for errors in the response
            
            file_path = os.path.join(settings.TEMP_DIR, f'{prefix_file_name}-{uuid4().hex}.{extension}')
            with open(file_path, "wb") as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)

            return file_path

        except requests.RequestException as e:
            raise e
    
    def run_ffmpeg_command(self, command):
        
        print(f'Running command: \n{command}')
        
        # Run the command and stream logs
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )

        # Stream the logs
        for line in iter(process.stdout.readline, ''):
            print(line.strip())

        process.wait()
        
    
general_service = GeneralService()
