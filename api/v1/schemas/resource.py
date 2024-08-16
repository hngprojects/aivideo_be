from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class CreateResource(BaseModel):
    """Schema for creating Resource"""

    title: str
    content: str
    image_url: str


class ResourceBase(CreateResource):
    """Base schema for Resource"""

    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UpdateResource(BaseModel):
    """Schema for updating Resource"""

    title: Optional[str] = None
    content: Optional[str] = None
    image_url: Optional[str] = None
