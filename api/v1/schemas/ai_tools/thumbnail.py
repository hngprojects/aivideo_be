from pydantic import BaseModel
from typing import List, Optional


class ProcessData(BaseModel):
    job_id: str
    project_id: str


class ThumbnailResponse(BaseModel):
    status_code: int
    success: bool
    message: str
    data: ProcessData


class YouTubeVideoRequest(BaseModel):
    youtube_url: str


class ThumbnailRequest(BaseModel):
    video_id: str
    timestamp: Optional[float] = None
    title: Optional[str] = None


class ThumbnailSelectionRequest(BaseModel):
    thumbnail_id: str
