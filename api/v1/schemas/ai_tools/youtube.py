from pydantic import BaseModel
from typing import List


class VideoLinkRequest(BaseModel):

    link: str
    detail_level: str = 'short'

class YTLinksRequest(BaseModel):
    """Youtube batch upload request body"""

    links: List[str]
    detail_level: str = 'short'
