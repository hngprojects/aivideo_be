from pydantic import BaseModel
from typing import Optional

class HelpCenterCreate(BaseModel):
    """
    Pydantic model for creating a new help center topic.
    """
    title: str
    description: Optional[str] = None

    class Config:
        from_attributes = True
        populate_by_name = True