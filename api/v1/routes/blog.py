from fastapi import Depends, HTTPException, APIRouter, status
from sqlalchemy.orm import Session
from api.v1.models.blog import Blog
from api.v1.schemas.blog import BlogSchema, BlogCreate, BlogUpdate
from api.v1.services.blog import blog_service
from api.utils.pagination import paginated_response
from api.utils.success_response import success_response
from api.db.database import get_db
from api.v1.models.user import User
from api.v1.services.user import user_service

blog = APIRouter(prefix="/blog", tags=["Blog"])


@blog.get("/available")
def read_available_blogs(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):

    return paginated_response(
        db,
        skip=skip,
        model=Blog,
        limit=limit,
        filters={'is_deleted': False}
    )


@blog.get("/deleted")
def read_available_blogs(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):

    return paginated_response(
        db,
        skip=skip,
        model=Blog,
        limit=limit,
        filters={'is_deleted': True}
    )


@blog.get("/{blog_id}", response_model=BlogSchema)
def read_blog(blog_id: str, db: Session = Depends(get_db)):
    blog = blog_service.fetch(db, blog_id)

    return success_response(
        status_code=status.HTTP_200_OK,
        message="Blog fetched successfully",
        data=blog
    )


@blog.get("")
def read_blogs(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):

    return paginated_response(
        db,
        skip=skip,
        model=Blog,
        limit=limit
    )


@blog.post("", response_model=BlogSchema)
def create_blog(
    blog: BlogCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(user_service.get_current_super_admin)
):
    blog = blog_service.create(db, blog)
    
    return success_response(
        status_code=status.HTTP_201_CREATED,
        message="Blog created successfully",
        data=blog
    )


@blog.put("/{blog_id}", response_model=BlogSchema)
def update_blog(
    blog_id: str,
    blog_update: BlogUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(user_service.get_current_super_admin)
):
    updated_blog = blog_service.update(db, blog_id, blog_update)
    
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Blog updated successfully",
        data=updated_blog
    )


@blog.delete("/{blog_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_blog(
    blog_id: str,
    db: Session = Depends(get_db),
    current_admin: User = Depends(user_service.get_current_super_admin)
):
    blog_service.delete(db, blog_id)
