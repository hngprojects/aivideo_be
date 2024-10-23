from fastapi import HTTPException
import requests
from api.utils.settings import settings


class StockMediaService:
    
    def __init__(self, query: str, page: int, per_page: int):
        """Initializer function for the stock service

        Args:
            query (str): This is the thing to search for in the stock apis. Must not exceed 100 characters
            page (int): Page number. Defaults to one
            per_page (int): Number of media to be retrieved from the API
        """
        
        self.query = query
        self.page = page
        self.per_page = per_page
        
    
    def __build_request(self, url: str, headers={}):
        """Helper function to build the request url"""
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.ConnectionError as e:
            raise HTTPException(status_code=500, detail='Network error. Please connect to a stable network')
        
        except requests.exceptions.Timeout as e:
            raise HTTPException(status_code=500, detail='Connection timeout')
        
        except requests.exceptions.RequestException as e:
            raise e
        
        except Exception as e:
            raise e   
             

    def __unsplash(self):
        """This function retrieves images from Unaplash API

        Args:
            page (int): Page number. Defaults to one
            per_page (int): Number of media to be retrieved from the API
        """
        
        api_key = settings.UNSPLASH_ACCESS_KEY
        url = f"https://api.unsplash.com/search/photos?query={self.query}&client_id={api_key}&page={self.page}&per_page={self.per_page}"
        
        data = self.__build_request(url)
        image_data: list = data['results']
        
        final_result = [{
            'preview': image['urls']['thumb'],
            'normal': image['urls']['raw']
        } for image in image_data] if image_data else []
        
        return final_result

    
    def __pixabay(self, media_type: str):
        """This function retrieves images and videos from Pixabay API

        Args:
            page (int): Page number
            per_page (int): Number of media to be retrieved from the API
            media_type (str): Should be one of `image` or `video`
        """
        
        api_key = settings.PIXABAY_API_KEY
        final_result = []

        if media_type == 'image':
            url = f"https://pixabay.com/api/?key={api_key}&q={self.query.replace(' ', '+')}&page={self.page}&per_page={self.per_page}&image_type=photo"
            data = self.__build_request(url)
            
            image_data: list = data['hits']
            final_result = [{
                'preview': image['previewURL'],
                'normal': image['webformatURL']
            } for image in image_data] if image_data else []
                    
        elif media_type == 'video':
            url = f"https://pixabay.com/api/videos/?key={api_key}&q={self.query.replace(' ', '+')}&page={self.page}&per_page={self.per_page}"
            
            data = self.__build_request(url)
            
            video_data: list = data['hits']
            final_result = [{
                'preview': video['videos']['medium']['thumbnail'],
                'normal': video['videos']['medium']['url'],
            } for video in video_data] if video_data else []
        
        return final_result
    
    
    def __pexels(self, media_type: str):
        """This function retrieves images and videos from Pexels API

        Args:
            page (int): Page number
            per_page (int): Number of media to be retrieved from the API
            media_type (str): Should be one of `image` or `video`
        """
        
        api_key = settings.PEXELS_API_KEY
        headers = {'Authorization': api_key}
        final_result = []
        
        if media_type == 'image':
            url = f"https://api.pexels.com/v1/search?query={self.query}&per_page={self.per_page}&page={self.page}"
            data = self.__build_request(url, headers)
            
            image_data: list = data['photos']
            final_result = [{
                'preview': image['src']['small'],
                'normal': image['src']['original']
            } for image in image_data] if image_data else []
                    
        elif media_type == 'video':
            url = f"https://api.pexels.com/videos/search?query={self.query}&per_page={self.per_page}&page={self.page}"
            data = self.__build_request(url, headers)
            
            video_data: list = data['videos']
            final_result = [{
                'preview': video['video_pictures'][0]['picture'],
                'normal': video['video_files'][0]['link']
            } for video in video_data] if video_data else []
        
        return final_result
    
    
    def fetch_images(self):
        images = []
        
        unsplash_images = self.__unsplash()
        pexels_images = self.__pexels('image')
        pixabay_images = self.__pixabay('image')
        
        images.extend(unsplash_images)
        images.extend(pexels_images)
        images.extend(pixabay_images)
        
        return images
    
    
    def fetch_videos(self):
        videos = []
        
        pexels_videos = self.__pexels('video')
        pixabay_videos = self.__pixabay('video')
        
        videos.extend(pexels_videos)
        videos.extend(pixabay_videos)
        
        return videos
