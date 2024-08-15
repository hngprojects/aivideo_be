from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class CreateTestimonialSchema(BaseModel):
    """Schema for creating Testimonials"""
    content: str
    rating: float
    client_name: str

class TestimonialBase(CreateTestimonialSchema):
    """Base schema for Testimonials"""

    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class UpdateTestimonialSchema(BaseModel):
    """Schema for updating Testimonials"""
    content: Optional[str] = None
    rating:  Optional[float] = None
    client_name: Optional[str] = None