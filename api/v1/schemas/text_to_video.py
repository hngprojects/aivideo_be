from pydantic import (BaseModel, StringConstraints,
                      Field, model_validator)
from typing import Optional, Annotated

text_input = "masterpiece, cinematic, man smoking cigarette looking outside window, moving around"

class TextInput(BaseModel):
    """
    Schema for text input
    """
    text: Annotated[
        Optional[str],
        StringConstraints(
            min_length=3,
            max_length=150,
            strip_whitespace=True
        )
    ] = Field(default=text_input)

class TextInputData(BaseModel):
    """
    Schema for text input data
    """
    task_id: Annotated[
        str,
        StringConstraints(
            min_length=1,
            max_length=150,
            strip_whitespace=True
        )
    ]
    status: Annotated[
        Optional[str],
        StringConstraints(
            min_length=3,
            max_length=20,
            strip_whitespace=True
        )
    ] = Field(default='Task is in queue')

    video_url: Optional[str] = None

class TextInputResponse(BaseModel):
    """
    Schema for text input response
    """
    message: str
    status_code: int
    data: TextInputData

class VideoTask(BaseModel):
    """
    Schema for videodata response
    """
    task_id: Annotated[
        str,
        StringConstraints(
            min_length=3,
            max_length=150,
            strip_whitespace=True
        )
    ]
    status: Annotated[
        str,
        StringConstraints(
            min_length=3,
            max_length=150,
            strip_whitespace=True
        )
    ] = Field(default='pending')
    user_id: Annotated[
        str,
        StringConstraints(
            min_length=3,
            max_length=150,
            strip_whitespace=True
        )
    ] = None
    video_url: Optional[str] = None

class VideoStatusResponse(BaseModel):
    """
    Schema for video response
    """
    status_code: int
    message: str = Field(default='successful')
    data: VideoTask


class VideoPatchRequest(BaseModel):
    """
    Schema for video patch
    """
    text: Annotated[
        str,
        StringConstraints(
            min_length=10,
            max_length=150,
            strip_whitespace=True
        )
    ] = Field(default=text_input)
    voice_over: Optional[str] = Field(default='none')
    task_id: Annotated[
        str,
        StringConstraints(
            min_length=10,
            max_length=60,
            strip_whitespace=True
        )
    ]


    @model_validator(mode='before')
    @classmethod
    def validate_data(cls, values:dict):
        """
        Validates data
        """
        voice_over: str = values.get("voice_over")

        if voice_over:
            choices = ['male', 'female', 'none', 'man', 'woman']
            if voice_over.lower() == 'man':
                values['voice_over'] = 'male'
            if voice_over.lower() == 'woman':
                values['voice_over'] = 'female'

            if voice_over.lower() not in choices:
                values['voice_over'] = 'none'
            if not voice_over:
                values['voice_over'] = 'none'
        return values
