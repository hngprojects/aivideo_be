from pydantic import BaseModel
from typing import List, Optional


class VideoLinkRequest(BaseModel):
    link: str


class PdfDownloadRequest(BaseModel):
    transcript: Optional[str] = None
    summary: Optional[str] = None
    video_title: Optional[str] = None


class YTLinksRequest(BaseModel):
    """Youtube batch upload request body"""

    links: List[str]
