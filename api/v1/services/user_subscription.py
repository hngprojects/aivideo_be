from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from typing import Any, Optional

from api.v1.services.user import user_service
from api.utils.pagination import get_pagination_details
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

    def fetch_all(self, db: Session, offset: int = 0, limit: int = 0, **query_params: Optional[Any]):
        """Fetch all user subscriptions with option to search using query parameters"""

        query = db.query(UserSubscription)

        # Enable filter by query parameter
        if query_params:
            for column, value in query_params.items():
                if hasattr(UserSubscription, column) and value:
                    query = query.filter(
                        getattr(UserSubscription, column).ilike(f"%{value}%")
                    )

        if limit and offset:
            user_subs = query.offset(offset).limit(limit).all()
        else:
            user_subs = query.all()

        return user_subs
    
    def dictize_user_subscriptions_and_pagination(
            self, user_subscriptions: list, offset: 0, limit: 0):
        """Return a list of dicts of all UserSubscription objs in 
        `user_subscriptions` and details of pagination for the list"""
        data = {
            "user_subscriptions": [
                {
                    **user_sub.to_dict(),
                    "is_active": user_sub.is_active(),
                    "price": user_sub.billing_plan.price,
                    "currency": user_sub.billing_plan.currency,
                    "plan_name": user_sub.billing_plan.plan_name,
                    "user_name": user_service.get_fullname(user_sub.user)
                } 
                for user_sub in user_subscriptions
            ],
            "pagination": get_pagination_details(len(user_subscriptions), offset, limit)
        }
        return data

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
