from fastapi import (
    APIRouter, Depends, HTTPException, status, 
    HTTPException, Response, Request
)
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from typing import Annotated

from api.db.database import get_db
from api.utils.pagination import paginated_response
from api.utils.success_response import success_response
from api.v1.models.user import User
from api.v1.models.blog import Blog
from api.v1.schemas.blog import (
    BlogCreate,
    BlogPostResponse,
    BlogUpdateResponseModel,
    BlogRequest
)
from api.v1.services.blog import BlogService
from api.v1.services.user import user_service

blog = APIRouter(prefix="/blogs", tags=["Blog"])


@blog.post("/", response_model=success_response)
def create_blog(
    current_user: Annotated[User, Depends(user_service.get_current_super_admin)],
    blog: BlogCreate,
    db: Session = Depends(get_db),
    
):
    blog_service = BlogService(db)
    new_blogpost = blog_service.create(db=db, schema=blog, author_id=current_user.id)

    return success_response(
        message="Blog created successfully!",
        status_code=201,
        data=jsonable_encoder(new_blogpost),
    )

@blog.get("/", response_model=success_response)
def get_all_blogs(db: Session = Depends(get_db), limit: int = 10, skip: int = 0):
    """Endpoint to get all blogs"""

    return paginated_response(
        db=db,
        model=Blog,
        limit=limit,
        skip=skip,
    )

@blog.get("/{id}", response_model=BlogPostResponse)
def get_blog_by_id(id: str, db: Session = Depends(get_db)):
    """
    Retrieve a blog post by its Id.

    Args:
        id (str): The ID of the blog post.
        db (Session): The database session.

    Returns:
        BlogPostResponse: The blog post data.

    Raises:
        HTTPException: If the blog post is not found.
    """
    blog_service = BlogService(db)

    blog_post = blog_service.fetch(id)

    return success_response(
        message="Blog post retrieved successfully!",
        status_code=200,
        data=jsonable_encoder(blog_post),
    )

@blog.put("/{id}", response_model=BlogUpdateResponseModel)
async def update_blog(
    id: str,
    blogPost: BlogRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(user_service.get_current_super_admin),
):
    """Endpoint to update a blog post"""

    blog_service = BlogService(db)
    updated_blog_post = blog_service.update(
        blog_id=id,
        title=blogPost.title,
        content=blogPost.content,
        # thumbnail_url=blogPost.thumbnail_url,
        subtitle=blogPost.subtitle
    )

    return success_response(
        message="Blog post updated successfully",
        status_code=200,
        data=jsonable_encoder(updated_blog_post),
    )