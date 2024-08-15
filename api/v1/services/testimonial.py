from typing import Any, Optional
from sqlalchemy.orm import Session
from api.core.base.services import Service
from api.v1.models.testimonial import Testimonial
from api.v1.schemas.testimonial import CreateTestimonialSchema, UpdateTestimonialSchema

class TestimonialService(Service):
    '''Testimonial service functionality'''

    def create(self, db: Session, schema: CreateTestimonialSchema) -> Testimonial:
        """Create a new testimonial

        Returns:
            (Testimonial): Testimonial object.
        """
        new_testimonial = Testimonial(**schema.model_dump())
        db.add(new_testimonial)
        db.commit()
        db.refresh(new_testimonial)

        return new_testimonial

    def fetch_all(self, db: Session, **query_params: Optional[Any]) -> list:
        """Fetch all testimonials with option to search using query parameters

        Returns:
            (list): A list of all testimonial objects present in the database
        """        
        query = db.query(Testimonial)

        # Enable filter by query parameter
        if query_params:
            for column, value in query_params.items():
                if hasattr(Testimonial, column) and value:
                    query = query.filter(getattr(Testimonial, column).ilike(f"%{value}%"))

        return query.all()

    def fetch(self, db: Session, testimonial_id: str) -> Testimonial | None:
        """Fetches a testimonial by id

        Args:
            db (Session): db Session Object
            testimonial_id (str): Testimonial id

        Returns:
            Testimonial
        """        
        testimonial = db.query(Testimonial).filter_by(id=testimonial_id).first()
        return testimonial

    def update(self, db: Session, testimonial_id: str, schema: UpdateTestimonialSchema) -> Testimonial | None:
        """Updates a Testimonial

        Args:
            db (Session): db Session object
            testimonial_id (str)
            schema (UpdateTestimonialSchema): Pydantic schema object 

        Returns:
            Testimonial
        """
        testimonial = self.fetch(db=db, testimonial_id=testimonial_id)
        if not testimonial:
            return None

        # Update the fields with the provided schema data
        update_data = schema.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(testimonial, key, value)

        db.commit()
        db.refresh(testimonial)
        return testimonial

    def delete(self, db: Session, testimonial_id: str) -> bool:
        """Deletes an Testimonial

        Args:
            db (Session)
            testimonial_id (str)

        Returns:
            bool: True if testimonial object is found else False
        """
        testimonial = self.fetch(db=db, testimonial_id=testimonial_id)

        if testimonial is None:
            return False

        db.delete(testimonial)
        db.commit()

        return True


testimonial_service = TestimonialService()