from pydantic import BaseModel, field_validator


class TalkingHeadRequest(BaseModel):

    script: str
    image_type: str
    # default: bool
    # avatar_id: str
    # avatar_img: str
    # voice_id: str

    @field_validator("image_type")
    def check_image_type(cls, value):
        allowed_types = ["horizontal", "vertical", "square"]
        if value not in allowed_types:
            raise ValueError(f"Invalid image type: {value}. Must be one of {', '.join(allowed_types)}.")
        return value
    