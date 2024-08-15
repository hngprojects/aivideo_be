from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class CreateTestimonialSchema(BaseModel):
    """Schema for creating Testimonials"""
    content: str
    rating: float
    client_name: str
    client_position: str
    avatar_url: Optional[str] = None

class TestimonialBase(CreateTestimonialSchema):
    """Base schema for Testimonials"""

    id: str
    updated_at: datetime
    
    class Config:
        from_attributes = True

class UpdateTestimonialSchema(BaseModel):
    """Schema for updating Testimonials"""
    content: Optional[str] = None
    rating:  Optional[float] = None
    client_name: Optional[str] = None
    client_position: Optional[str] = None
    avatar_url: Optional[str] = None
