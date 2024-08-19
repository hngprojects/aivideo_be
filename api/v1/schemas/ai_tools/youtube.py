from pydantic import BaseModel
from typing import Optional


class VideoLinkRequest(BaseModel):
    link: str


class PdfDownloadRequest(BaseModel):
    transcript: str
    summary: str
    video_title: Optional[str] = None
