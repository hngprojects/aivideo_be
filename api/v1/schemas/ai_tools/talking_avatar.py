from pydantic import BaseModel, field_validator


class TalkingHeadRequest(BaseModel):

    avatar_id: str
    audio_id: str
    script: str
    aspect_ratio: str
    voice_over: str

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
    

class DownloadRequest(BaseModel):

    file_url: str