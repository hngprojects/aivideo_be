from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class BlogCreate(BaseModel):
    title: str = Field(..., max_length=100)
    subtitle: Optional[str] = None
    content: str
    thumbnail_url: Optional[str] = None
    tags: Optional[List[str]] = None
    excerpt: Optional[str] = Field(None, max_length=500)