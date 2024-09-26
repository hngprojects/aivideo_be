from pydantic import BaseModel
from typing import Union, Optional

class TranslationRequest(BaseModel):

    text: Union[str, dict]
    target_language: str
    

class PodcastRequest(BaseModel):
    
    podcast_url: str
    detail_level: Optional[str] = 'short'
    