from typing import List
from pydantic import BaseModel, field_validator


class TTVSchema(BaseModel):

    script: str
    audio_id: str
    aspect_ratio: str
    voice_over: str
    scenes: List[str]

    @field_validator("aspect_ratio")
    def check_image_type(cls, value):
        allowed_types = ["horizontal", "vertical", "square"]
        if value not in allowed_types:
            raise ValueError(f"Invalid image type: {value}. Must be one of {', '.join(allowed_types)}.")
        return value
    
    @field_validator("voice_over")
    def check_voice_over(cls, value):
        allowed_types = ["man", "woman", "neutral"]
        if value not in allowed_types:
            raise ValueError(f"Invalid voice over: {value}. Must be one of {', '.join(allowed_types)}.")
        return value
    
    @field_validator("scenes")
    def check_length_of_scenes_list(cls, value):
        if len(value) < 2:
            raise ValueError("Number of scenes cannot be less than two")
        return value

 
class SceneGeneration(BaseModel):

    script: str
    