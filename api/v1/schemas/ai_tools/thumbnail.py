from pydantic import BaseModel
from typing import List


class YouTubeVideoRequest(BaseModel):
    youtube_url: str


class ManualCaptureThumbnailRequest(BaseModel):
    video_id: str
    timestamp: float


class ThumbnailSelectionRequest(BaseModel):
    thumbnail_id: str
    resolution: str
