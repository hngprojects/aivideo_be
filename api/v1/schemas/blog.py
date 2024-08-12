from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, HttpUrl
from uuid_extensions import uuid7

class BlogCreate(BaseModel):
    title: str = Field(..., max_length=100)
    subtitle: Optional[str] = None
    content: str
    thumbnail_url: Optional[str] = None
    tags: Optional[List[str]] = None
    excerpt: Optional[str] = Field(None, max_length=500)

class BlogPostResponse(BaseModel):

    subtitle: str
    title: str
    excerpt: str
    id: uuid7
    updated_at: datetime
    content: str
    author_id: uuid7
    thumbnail_url: HttpUrl
    tags: List[str]
    created_at: datetime

    class Config:
        from_attributes = True