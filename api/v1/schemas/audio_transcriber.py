from pydantic import BaseModel

class TranslationRequest(BaseModel):
    text: str
    target_language: str

class PodcastRequest(BaseModel):
    podcast_url: str