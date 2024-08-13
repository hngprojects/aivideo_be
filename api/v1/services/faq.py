from typing import Any, Optional
from sqlalchemy.orm import Session
from api.core.base.services import Service
from api.v1.models.faq import FAQ
from api.v1.schemas.faq import CreateFAQ, UpdateFAQ

class FAQService(Service):
    '''FAQ service functionality'''

    def create(self, db: Session, schema: CreateFAQ) -> FAQ:
        """Create a new FAQ

        Returns:
            (FAQ): FAQ object.
        """
        new_faq = FAQ(**schema.model_dump())
        db.add(new_faq)
        db.commit()
        db.refresh(new_faq)

        return new_faq

    def fetch_all(self, db: Session, **query_params: Optional[Any]) -> list:
        """Fetch all FAQs with option to search using query parameters

        Returns:
            (list): A list of all faq objects present in the database
        """        
        query = db.query(FAQ)

        # Enable filter by query parameter
        if query_params:
            for column, value in query_params.items():
                if hasattr(FAQ, column) and value:
                    query = query.filter(getattr(FAQ, column).ilike(f"%{value}%"))

        return query.all()

    def fetch(self, db: Session, faq_id: str) -> FAQ | None:
        """Fetches a, FAQ by id

        Args:
            db (Session): db Session Object
            faq_id (str): Faq id

        Returns:
            FAQ
        """        
        faq = db.query(FAQ).filter_by(id=faq_id).first()
        return faq

    def update(self, db: Session, faq_id: str, schema: UpdateFAQ) -> FAQ | None:
        """Updates an FAQ

        Args:
            db (Session): db Session object
            faq_id (str)
            schema (UpdateFAQ): Pydantic schema object 

        Returns:
            FAQ
        """
        faq = self.fetch(db=db, faq_id=faq_id)
        if not faq:
            return None

        # Update the fields with the provided schema data
        update_data = schema.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(faq, key, value)

        db.commit()
        db.refresh(faq)
        return faq

    def delete(self, db: Session, faq_id: str) -> bool:
        """Deletes an FAQ

        Args:
            db (Session)
            faq_id (str)

        Returns:
            bool: True if faq object is found else False
        """
        faq = self.fetch(db=db, faq_id=faq_id)

        if faq is None:
            return False

        db.delete(faq)
        db.commit()

        return True


faq_service = FAQService()