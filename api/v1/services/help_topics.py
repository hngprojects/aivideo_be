from typing import List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from api.v1.models.help_topics import HelpTopics
from api.v1.schemas.help_topics import HelpCenterCreate


class HelpTopicsService:
    """Help Topics Services"""

    @staticmethod
    def fetch_all(db: Session) -> List[HelpTopics]:
        return db.query(HelpTopics).all()

    @staticmethod
    def create(db: Session, schema: HelpCenterCreate) -> HelpTopics:
        try:
            help_topic = HelpTopics(title=schema.title, description=schema.description)
            db.add(help_topic)
            db.commit()
            db.refresh(help_topic)
            return help_topic
        except Exception:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred."
            )
        
    @staticmethod
    def delete_all(db: Session):
        try:
            db.query(HelpTopics).delete()
            db.commit()
        except Exception:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred."
            )  