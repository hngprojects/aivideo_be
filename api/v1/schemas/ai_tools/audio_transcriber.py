from pydantic import BaseModel
from typing import Union

class TranslationRequest(BaseModel):
    text: Union[str, dict]
    target_language: str

class PodcastRequest(BaseModel):
    podcast_url: str