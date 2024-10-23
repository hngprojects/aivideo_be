from typing import List

from api.utils.openai_service import openai_service
from api.v1.services.ai_tools.general import general_service


class TweetToTiktokService:
    
    def generate_scene_descriptions(self, script: str):
        
        response = openai_service.prompt_ai(
            prompt=f'Generate five simple and short scene descriptions not more than 100 characters that can be used as an image description for AI and stock images and videos API query for the following script and I do not want any form of numbering or bulleting on them. Also, do not say any other thing other than the scene descriptions. Here is the script: :\n\n{script}\n\nScene Descriptions:',
            system_role_desc='You are a great scene description generator.'
        )
        
        scenes = [scene.strip() for scene in response.strip().split('\n') if scene.strip()]
        return scenes
    
    
    def download_media(self, urls: List[str]):
        '''This function is used to dwonload media files'''
        
        save_paths = []
        for url in urls:
            if 'photo' in url or 'jpg' in url or 'png' in url or 'jpeg' in url:
                save_extension = 'jpg'
            elif 'video' in url or 'mp4' in url:
                save_extension = 'mp4'
            else:
                continue  # Skip unsupported media types
                
            file_path = general_service.download_file(url, extension=save_extension)
            save_paths.append(file_path)

        return save_paths
    
    
    def convert_to_video(self):
        pass    
        
        

tweet_to_tiktok_service = TweetToTiktokService()
