from typing import Optional, List
from pydantic import  HttpUrl
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

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
    
    def fetch_all(self):
        """Fetch all blog posts"""

        blogs = self.db.query(Blog).filter(Blog.is_deleted == False).all()
        return blogs
    
    def fetch(self, blog_id: str):
        """Fetch a blog post by its ID"""

        blog_post = self.db.query(Blog).filter(Blog.id == blog_id).first()
        if not blog_post:
            raise HTTPException(status_code=404, detail="Post not found")
        return blog_post
    
    def update(
        self,
        blog_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        subtitle: Optional[str] = None,
        # thumbnail_url: Optional[HttpUrl] = None
    ):
        """Updates a blog post"""

        if not title or not content:
            raise HTTPException(
                status_code=400, detail="Title and content cannot be empty"
            )

        blog_post = self.fetch(blog_id)

        # Update the fields with the provided data
        blog_post.title = title
        blog_post.content = content
        blog_post.subtitle = subtitle
        # blog_post.thumbnail_url = thumbnail_url


        try:
            self.db.commit()
            self.db.refresh(blog_post)
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=500, detail="An error occurred while updating the blog post"
            )

        return blog_post
    
    def delete(self, blog_id: str):
        """Delete a blog post by its ID"""
        post = self.fetch(blog_id=blog_id)

        if not post:
            raise HTTPException(
                status_code=404,
                detail="Blog post not found",
            )

        try:
            self.db.delete(post)
            self.db.commit()
        except SQLAlchemyError as e:
            self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail="An error occurred while deleting the blog post",
            )