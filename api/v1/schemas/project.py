from pydantic import BaseModel
from typing import Optional, Union
from datetime import datetime


class CreateProject(BaseModel):

    title: str
    project_type: str


class UpdateProject(BaseModel):

    title: str
    description: str


class CreateFullProjectSchema(CreateProject):
    description: Optional[str] = None
    file_url: Optional[str] = None
    result: Optional[str] = None


class UpdateProjectSchema(BaseModel):
    title: Optional[str] = None
    project_type: Optional[str] = None
    description: Optional[str] = None
    file_url: Optional[str] = None
    result: Optional[str] = None


class AddFullProjectSchema(CreateFullProjectSchema):
    user_id: str


class ProjectCreateResponseSchema(CreateFullProjectSchema):
    id: str
    updated_at: datetime

    class Config:
        from_attributes = True

class ToolStatsData(BaseModel):
    pdf_summarizer: float
    podcast_summarizer: float
    youtube_summarizer: float
    audio_transcriber: float
    text_to_video: float
    image_to_video: float
    thumbnail_generator: float

class ToolStatsResponse(BaseModel):
    message: str
    status_code: int
    status: str
    data: Union[ToolStatsData, None]
