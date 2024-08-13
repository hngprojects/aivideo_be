from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional


class UserResponse(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    updated_at: datetime


class JobsResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    file_url: str
    size: str
    status: str
    duration: str
    project_type: str
    user: UserResponse
    created_at: datetime
    updated_at: datetime
    archived: bool
    archived_at: Optional[datetime]
    is_deleted: bool


class PaginatedResponse(BaseModel):
    pages: int
    total: int
    skip: int
    limit: int
    items: List[JobsResponse]
