from datetime import datetime
from typing import Optional
from pydantic import BaseModel



class CreateFAQ(BaseModel):
    """Schema for creating FAQ"""

    question: str
    answer: str
    category: str

class FAQBase(CreateFAQ):
    """Base schema for FAQ"""

    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class UpdateFAQ(BaseModel):
    """Schema for updating FAQ"""

    question: Optional[str] = None
    answer: Optional[str] = None
    category: Optional[str] = None