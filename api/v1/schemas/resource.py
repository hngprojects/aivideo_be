from datetime import datetime
from typing import Optional, Union, List
from pydantic import BaseModel


class SuccessResponse(BaseModel):
    status: str = "success"
    status_code: int = 201
    message: str

class CreateResource(BaseModel):
    """Schema for creating Resource"""

    title: str
    content: str
    image_url: Optional[str]
    cover_image_url: Optional[str]
    tags: Optional[List[str]]


class ResourceBase(CreateResource):
    """Base schema for Resource"""

    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ResourceData(ResourceBase):
    """Data schema for resources"""

    is_deleted: bool = False
    is_published: bool = False


class UpdateResource(BaseModel):
    """Schema for updating Resource"""

    title: Optional[str] = None
    content: Optional[str] = None
    image_url: Optional[str] = None
    cover_image_url: Optional[str] = None
    tags: Optional[List[str]] = None

class CreateResourceResponse(SuccessResponse):
    data: ResourceData


class AllResourcesResponse(BaseModel):
    """
    Schema for all resources
    """

    message: str
    status_code: int
    status: str
    page: int
    per_page: int
    total_pages: int
    total: int
    data: Union[List[ResourceData], List[None]]
