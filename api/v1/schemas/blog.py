from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field



class BlogBase(BaseModel):
    title: str
    content: str
    image_url: Optional[str] = None
    cover_image_url: Optional[str] = None
    is_deleted: Optional[bool] = False
    category: str


class BlogCreate(BlogBase):
    pass

class BlogUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    image_url: Optional[str] = None
    cover_image_url: Optional[str] = None
    is_deleted: Optional[bool] = None
    category: Optional[str] = None

class BlogSchema(BlogBase):
    id: int

    class Config:
        from_attribute = True

