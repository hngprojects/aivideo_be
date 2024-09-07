from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from api.utils.db_validators import check_model_existence
from api.v1.models.blog import Blog
from api.v1.schemas.blog import BlogCreate, BlogUpdate


class BlogService:
    """Blog service functionality"""

    def create(self, db: Session, schema: BlogCreate):
        """Create a blog"""

        blog = Blog(**schema.model_dump())
        db.add(blog)
        db.commit()
        db.refresh(blog)
        return blog

    def fetch_all(self, db: Session):
        """Fetch all blogs"""

        blogs = db.query(Blog).filter(Blog.is_deleted == False).all()
        return blogs

    def fetch(self, db: Session, blog_id: str):
        """Fetch a blog by its ID"""
    
        blog = check_model_existence(db, Blog, blog_id)
        if not blog.is_deleted:
            return blog
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Blog not found"
            )

    def update(self, db: Session, blog_id: str, blog_update: BlogUpdate):
        """
        Update a blog post in the database.

        Parameters:
        db (Session): The database session object from SQLAlchemy.
        blog_id (str): The unique identifier of the blog post to be updated.
        blog_update (BlogUpdate): An instance of BlogUpdate schema containing the updated data.

        Returns:
        Optional[Blog]: The updated blog post if found and updated successfully.
                        Returns None if the blog post is not found.
        """
        blog = self.fetch(db, blog_id=blog_id)
        if not blog:
            return None

        for key, value in blog_update.dict(exclude_unset=True).items():
            setattr(blog, key, value)

        db.commit()
        db.refresh(blog)
        return blog

    def delete(self, db: Session, blog_id: str):
        """
        Delete a blog post from the database.

        Parameters:
        db (Session): The database session object from SQLAlchemy.
        blog_id (int): The unique identifier of the blog post to be deleted.

        Returns:
        Optional[Blog]: The deleted blog post if found and deleted successfully.
                        Returns None if the blog post is not found.
        """
        blog = self.fetch(db, blog_id=blog_id)
        if blog is None:
            return None

        blog.is_deleted = True
        db.commit()
        db.refresh(blog)
        return blog
    


blog_service = BlogService()