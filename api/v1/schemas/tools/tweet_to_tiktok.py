from typing import Optional, List
from fastapi import Form, UploadFile, File
from pydantic import BaseModel, field_validator

class TweetToTiktokRequest(BaseModel):

    # text: Optional[str] = None
    # tweet_link: Optional[str] = None
    # audio_id: Optional[str] = None
    # voice_over: str
    # scene_media_urls: List[str]
    # video_style: str
    
    text: Optional[str] = Form(None)
    tweet_link: Optional[str] = Form(None)
    audio_id: Optional[str] = Form(None)
    custom_audio: Optional[UploadFile] = File(...)
    voice_id: Optional[str] = Form(None)
    custom_voice: Optional[UploadFile] = File(...)
    scene_media_urls: List[str] = Form(...)
    video_style: str = Form(...)
    
    # @field_validator("voice_over")
    # def check_voice_over(cls, value):
    #     allowed_types = ["man", "woman", "neutral"]
    #     if value not in allowed_types:
    #         raise ValueError(f"Invalid voice over: {value}. Must be one of {', '.join(allowed_types)}.")
    #     return value
    
    @field_validator("scene_media_urls")
    def check_length_of_scene_media_urls_list(cls, value):
        if len(value) < 2:
            raise ValueError("Number of scene media links cannot be less than two")
        return value
    
    @field_validator("video_style")
    def check_video_style(cls, value):
        allowed_types = [
            "stock images",
            "stock videos", 
            "takling avatar",
            "ai images",
            "3d moving videos",
            "ai illustrations"
        ]
        
        if value not in allowed_types:
            raise ValueError(f"Invalid media type: {value}. Must be one of {', '.join(allowed_types)}.")
        
        return value



class SceneGeneration(BaseModel):
    script: str
