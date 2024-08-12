from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from api.v1.models.blog import Blog
from api.v1.models.user import User
from api.v1.schemas.blog import BlogCreate


class BlogService:
    """Blog service functionality"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, db: Session, schema: BlogCreate, author_id: str):
        """Create a new blog post"""

        new_blogpost = Blog(**schema.model_dump(), author_id=author_id)
        db.add(new_blogpost)
        db.commit()
        db.refresh(new_blogpost)
        return new_blogpost