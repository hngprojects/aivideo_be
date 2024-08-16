from pydantic import BaseModel
from typing import List, Optional


class YouTubeVideoRequest(BaseModel):
    youtube_url: str


class ThumbnailRequest(BaseModel):
    video_id: str
    manual_capture: Optional[bool] = False
    timestamp: Optional[float] = None


class ThumbnailSelectionRequest(BaseModel):
    thumbnail_id: str
    resolution: str
