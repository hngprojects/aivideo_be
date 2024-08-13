from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, HttpUrl
from uuid import UUID 

class BlogCreate(BaseModel):
    title: str = Field(..., max_length=100)
    subtitle: Optional[str] = None
    content: str
    thumbnail_url: Optional[HttpUrl] = None  
    tags: Optional[List[str]] = None
    excerpt: Optional[str] = Field(None, max_length=500)

class BlogPostResponse(BaseModel):
    id: UUID 
    title: str
    subtitle: Optional[str] = None
    excerpt: Optional[str] = None
    content: str
    author_id: UUID  
    thumbnail_url: Optional[HttpUrl] = None 
    tags: List[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True  

class BlogUpdateResponseModel(BaseModel):
    id: UUID  
    title: str
    subtitle: Optional[str] = None
    content: str
    thumbnail_url: Optional[HttpUrl] = None  
    excerpt: Optional[str] = None
    tags: Optional[List[str]] = None
    author_id: UUID  
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True  

class BlogRequest(BaseModel):
    title: str
    subtitle: Optional[str] = None
    content: str
    thumbnail_url: Optional[HttpUrl] = None  
    excerpt: Optional[str] = None
    tags: Optional[List[str]] = None

    class Config:
        orm_mode = True  
