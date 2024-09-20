from pydantic import BaseModel
from typing import List, Optional


class VideoLinkRequest(BaseModel):
    link: str


class PdfDownloadRequest(BaseModel):
    job_id: str
    language: str
    transcript: bool = True
    summary: bool = True
    video_title: Optional[str] = None


class YTLinksRequest(BaseModel):
    """Youtube batch upload request body"""

    links: List[str]
