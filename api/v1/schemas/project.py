from pydantic import BaseModel
from typing import Optional, Union
from datetime import datetime
from enum import Enum


class CreateProject(BaseModel):

    title: str
    project_type: str
    description: Optional[str] = None
    user_id: Optional[str] = None


class UpdateProject(BaseModel):

    title: str
    description: str


class CreateFullProjectSchema(CreateProject):
    file_url: Optional[str] = None
    result: Optional[str] = None
    thumbnail: Optional[str] = None


class UpdateProjectSchema(BaseModel):
    title: Optional[str] = None
    project_type: Optional[str] = None
    description: Optional[str] = None
    file_url: Optional[str] = None
    result: Optional[str] = None


class SaveProjectSchema(BaseModel):

    result: str


class AddFullProjectSchema(CreateFullProjectSchema):
    pass


class ProjectCreateResponseSchema(CreateFullProjectSchema):
    id: str
    updated_at: datetime

    class Config:
        from_attributes = True


class BaseResponseSchema(BaseModel):
    message: str
    status_code: int
    status: str


class SingleProjectResponse(BaseResponseSchema):
    """
    Schema for all Project Response
    """

    data: ProjectCreateResponseSchema | None


class AllProjectResponse(BaseResponseSchema):
    """
    Schema for all Project Response
    """

    data: Union[list[ProjectCreateResponseSchema], list[None]]


class ToolStatsData(BaseModel):
    pdf_summarizer: float = 0
    podcast_summarizer: float = 0
    youtube_summarizer: float = 0
    audio_transcriber: float = 0
    text_to_video: float = 0
    image_to_video: float = 0
    thumbnail_generator: float = 0


class ToolStatsResponse(BaseModel):
    message: str
    status_code: int
    status: str
    data: Union[ToolStatsData, None]


class ProjectToolsEnum(str, Enum):
    youtube_summarizer = "Youtube Summarizer"
    video_summarizer = "Video Summarizer"
    text_to_video = "Text To Video"
    talking_avatar = "Talking Avatar"
    audio_transcriber = "Audio Transcriber"
    audio_summarizer = "Audio Summarizer"
    image_to_video = "Image To Video"
    podcast_summarizer = "Podcast Summarizer"
    thumbnail_generator = "Thumbnail Generator"
    pdf_summarizer = "PDF Summarizer"
    subtitle_translator = "Subtitle Translator"
    audio_extractor = "Audio Extractor"
    video_format_conversion = "Video Format Compression"
    video_compression = "Video Compression"
    merge_videos = "Merge Videos"
