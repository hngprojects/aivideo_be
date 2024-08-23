from pydantic import BaseModel
from typing import List, Optional


class YouTubeVideoRequest(BaseModel):
    youtube_url: str


class ThumbnailRequest(BaseModel):
    video_id: str
    timestamp: Optional[float] = None
    title: Optional[str] = None


class ThumbnailSelectionRequest(BaseModel):
    thumbnail_id: str
