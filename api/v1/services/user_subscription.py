from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from typing import Any, Optional

from api.utils.db_validators import check_model_existence
from api.v1.models.user_subscription import UserSubscription
from api.v1.schemas.user_subscription import CreateUserSubSchema


class UserSubscriptionService:
    """UserSubscription service functionality"""

    def create(self, db: Session, schema: CreateUserSubSchema):
        """
        Create and return a new user subscription
        """
        if isinstance(schema, dict):
            user_sub = UserSubscription(**schema)
        else:
            user_sub = UserSubscription(**schema.dict())

        db.add(user_sub)
        db.commit()
        db.refresh(user_sub)

        return user_sub

    def fetch(self, db: Session, user_sub_id: str):
        """Fetch a single user subscription by id"""
        return check_model_existence(db, UserSubscription, user_sub_id) 

    def fetch_all(self, db: Session, **query_params: Optional[Any]):
        """Fetch all user subscriptions with option to search using query parameters"""

        query = db.query(UserSubscription)

        # Enable filter by query parameter
        if query_params:
            for column, value in query_params.items():
                if hasattr(UserSubscription, column) and value:
                    query = query.filter(
                        getattr(UserSubscription, column).ilike(f"%{value}%")
                    )

        return query.all()

    def delete(self, db: Session, user_sub_id: str):
        """
        Delete a user sub by id
        """
        user_sub = check_model_existence(db, UserSubscription, user_sub_id)

        db.delete(user_sub)
        db.commit()
    
    @staticmethod
    def get_sub_start_and_end_datetime(amount_paid, bill_amount):
        """Compute and return subcription end datetiem, with start datetime"""
        start_datetime = datetime.now(tz=timezone.utc)
        num_of_months = int(amount_paid // bill_amount)
        num_of_days = num_of_months * 30
        end_datetime = start_datetime + timedelta(days=num_of_days)
        return start_datetime, end_datetime


user_subscription_service = UserSubscriptionService()
