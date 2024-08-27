from datetime import datetime, timezone, timedelta
from typing import Any, Optional, Union
from sqlalchemy.orm import Session

from api.v1.services.user import user_service
from api.utils.pagination import get_pagination_details
from api.v1.models.user_subscription import UserSubscription
from api.v1.schemas.user_subscription import CreateUserSubSchema
from api.utils.db_validators import check_model_existence, get_model_by_params


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

    def fetch_by_params(self, db: Session, query_params: dict):
        """Fetches a user subscription by one or more query params"""
        user_sub = get_model_by_params(db, UserSubscription, query_params)
        return user_sub

    def fetch_by_user_and_plan(self, db: Session, user_id: str, billing_plan_id: str):
        """Fetches user subscription by user_id and billing_plan_id"""

        user_sub = db.query(UserSubscription).filter(
            UserSubscription.user_id == user_id,
            UserSubscription.billing_plan_id == billing_plan_id
            ).first()
        
        return user_sub

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

    @staticmethod
    def dynamic_user_subscription_dict(user_sub: UserSubscription):
        """Return `UserSubscription.to_dict()` with extra dynamic details, 
        eg: `'plan_name'`, `'user_name'`, `'is_active'` etc
        """

        user_sub_dict = {
            **user_sub.to_dict(),
            "is_active": user_sub.is_active(),
            "price": user_sub.billing_plan.price,
            "currency": user_sub.billing_plan.currency,
            "plan_name": user_sub.billing_plan.plan_name,
            "user_name": user_service.get_fullname(user_sub.user)
        } 

        return user_sub_dict
    
    def dictize_user_subscriptions_and_pagination(
            self, user_subscriptions: list, offset: 0, limit: 0):
        """Return a list of dicts of all UserSubscription objs in 
        `user_subscriptions` and details of pagination for the list"""
        data = {
            "user_subscriptions": [
                self.dynamic_user_subscription_dict(user_sub)
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
    def get_sub_start_and_end_datetime(amount_paid, bill_per_interval, free_plan=False):
        """Compute and return subcription end datetiem, with start datetime"""
        start_datetime = datetime.now(tz=timezone.utc)
        # If the plan if free_plan, set the duration to 12-months
        num_of_months = 12 if free_plan else int(amount_paid // bill_per_interval)
        num_of_days = num_of_months * 30
        end_datetime = start_datetime + timedelta(days=num_of_days)
        return start_datetime, end_datetime


user_subscription_service = UserSubscriptionService()
