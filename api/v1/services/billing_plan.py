from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from uuid_extensions import uuid7
from typing import Any, Optional

from api.v1.services.user_subscription import user_subscription_service as user_sub_serviec
from api.utils.db_validators import check_model_existence, get_model_by_params
from api.v1.schemas.billing_plan import CreateBillingPlanSchema
# from api.v1.models.user_subscription import UserSubscription
from api.v1.models.billing_plan import BillingPlan
from api.v1.models.user import User


class BillingPlanService:
    """Product service functionality"""

    def create(self, db: Session, schema: CreateBillingPlanSchema):
        """
        Create and return a new billing plan
        """
        try:
            plan = BillingPlan(id=str(uuid7()), **schema.model_dump())
            db.add(plan)
            db.commit()
            db.refresh(plan)
            return plan
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{type(e).__name__} occurred. {repr(e)}"
            )

    def fetch(self, db: Session, plan_id: str):
        """Fetch a single billing plan by id"""
        return check_model_existence(db, BillingPlan, plan_id)

    def fetch_by_params(self, db: Session, query_params: dict):
        """Fetches a billing plan by one or more query params"""
        bill_plan = get_model_by_params(db, BillingPlan, query_params)
        return bill_plan

    def fetch_all(self, db: Session, **query_params: Optional[Any]):
        """Fetch all billing plans with option to search using query parameters"""

        query = db.query(BillingPlan)

        # Enable filter by query parameter
        if query_params:
            for column, value in query_params.items():
                if hasattr(BillingPlan, column) and value:
                    query = query.filter(
                        getattr(BillingPlan, column).ilike(f"%{value}%")
                    )
        
        all_plans = query.all()

        return all_plans

    def update(self, db: Session, plan_id: str, schema):
        """
        Update a billing plan
        """
        plan = check_model_existence(db, BillingPlan, plan_id)

        update_data = schema.dict(exclude_unset=True)
        for column, value in update_data.items():
            setattr(plan, column, value)

        db.commit()
        db.refresh(plan)

        return plan

    def delete(self, db: Session, plan_id: str):
        """
        Delete a billing plan by id
        """
        plan = check_model_existence(db, BillingPlan, plan_id)

        db.delete(plan)
        db.commit()
    
    def subscribe_user_to_free_plan(self, db: Session, user: User):
        """Subscribe a user to free billing plan"""
        free_plan = self.fetch_by_params(db, {"plan_name": "Free"})
        if not free_plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Free billing plan not found. Please try again later"
            )
        
        # create a user subscription plan
        start_date, end_date = user_sub_serviec.get_sub_start_and_end_datetime(0, 0, free_plan=True)
        user_subscription_data = {
            "user_id": user.id,
            "end_date": end_date,
            "start_date": start_date,
            "billing_plan_id": free_plan.id,
        }
        user_sub = user_sub_serviec.create(db, user_subscription_data)

        return user_sub
    
    def confirm_user_is_on_plan(self, db: Session, user: User, plan_name: str):
        """Confirm that `user` is subscribed to billing plan with `plan_name`"""

        bill_plan = self.fetch_by_params(db, {"plan_name": plan_name})

        user_sub = user_sub_serviec.fetch_by_user_and_plan(db, user.id, bill_plan.id)
        
        if not user_sub:
            # If noe existing subscription, put user on
            # the free plan and check if `plan_name` is ""Free"
            _ = self.subscribe_user_to_free_plan(db, user)

            return plan_name == "Free"
        
        return user_sub.billing_plan.plan_name == plan_name


billing_plan_service = BillingPlanService()
