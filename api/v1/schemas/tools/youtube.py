from pydantic import BaseModel
from typing import List, Optional


class VideoLinkRequest(BaseModel):

    link: str
    detail_level: Optional[str] = 'short'

class YTLinksRequest(BaseModel):
    """Youtube batch upload request body"""

    links: List[str]
    detail_level: Optional[str] = 'short'
