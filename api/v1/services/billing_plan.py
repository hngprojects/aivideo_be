from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from uuid_extensions import uuid7
from typing import Any, Optional
import math

from api.v1.services.user_subscription import user_subscription_service as user_sub_service
from api.utils.db_validators import check_model_existence, get_model_by_params
from api.v1.schemas.billing_plan import CreateBillingPlanSchema
from api.v1.models.billing_plan import BillingPlan
from api.v1.models.user import User

class BillingPlanService:
    """Product service functionality"""

    YEARLY_PAYMENT_DISCOINT_PERCENT = 15
    NUMBER_OF_MONTHS_CHARGED_YEARLY = 10

    def load_billing_plans_in_db(self, db: Session,):

        try:
            free_plan = BillingPlan(
                plan_name="Free",
                price=0,
                access_limit=50,
                plan_interval='one-off',
                currency='USD',
                features=[
                    'Access to tools',
                    'Text to Video',
                    'Image to Video',
                    'Talking Avatar Generator',
                    'Youtube Summarizer',
                    'Podcast Summarizer',
                    'Limited Processing',
                    'Watermark on videos'
                ]
            )

            premium_monthly_plan = BillingPlan(
                plan_name="Premium Monthly",
                price=4.99,
                plan_interval='monthly',
                access_limit=150,
                currency='USD',
                features=[
                    'Access to tools',
                    'Text to Video',
                    'Image to Video',
                    'Talking Avatar Generator',
                    'Youtube Summarizer',
                    'Podcast Summarizer',
                    'Watermark free videos',
                    'Early access to new features',
                    'Early access to future tools'
                ]
            )

            premium_yearly_plan = BillingPlan(
                plan_name="Premium Yearly",
                price=49.99,
                plan_interval='yearly',
                access_limit=500,
                currency='USD',
                features=[
                    'Access to tools',
                    'Text to Video',
                    'Image to Video',
                    'Talking Avatar Generator',
                    'Youtube Summarizer',
                    'Podcast Summarizer',
                    'Watermark free videos',
                    'Early access to new features',
                    'Early access to future tools',
                    'Save 15% compared to monthly'
                ]
            )

            db.add(free_plan)
            db.add(premium_monthly_plan)
            db.add(premium_yearly_plan)
            db.commit()

            return db.query(BillingPlan).all()
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"An error occurred: {e}")
        finally:
            db.close()

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
        if len(all_plans) == 0:
            all_plans = self.load_billing_plans_in_db(db)
            
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
        """Subscribe a user to free billing plan irrespective 
        of the plan they are currently on"""

        free_plan = self.fetch_by_params(db, {"plan_name": "Free"})
        if not free_plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Free billing plan not found. Please try again later"
            )

        # check if user is already on free subscription
        user_sub = user.subscription
        if user_sub == free_plan:
            return user_sub
        
        # create a user subscription plan
        start_date, end_date = user_sub_service.get_sub_start_and_end_datetime(
            free_plan.plan_interval)
        user_subscription_data = {
            "user_id": user.id,
            "end_date": end_date,
            "start_date": start_date,
            "billing_plan_id": free_plan.id,
        }
        user_sub = user_sub_service.create(db, user_subscription_data)

        return user_sub
    
    def confirm_user_is_on_plan(self, db: Session, user: User, plan_name: str) -> bool:
        """Confirm that `user` is subscribed to billing plan with `plan_name`"""

        user_sub = user.subscription
        
        if user_sub is None:
            # If no existing subscription, put user on the free 
            # plan then check if `plan_name` being checked is "Free"
            _ = self.subscribe_user_to_free_plan(db, user)

            return plan_name == "Free"
        
        return user_sub.billing_plan.plan_name == plan_name
    
    def dynamic_billing_plan_dict(self, bill_plan: BillingPlan):
        """Return `BillingPlan.to_dict()` with extra dynamic details, 
        eg: `'yearly_discount_percent'`, `'yearly_total'`, etc
        """
        yearly_discount_percent = 0
        year_total = bill_plan.price
        if year_total:
            # get the 99.99 effect, instead of hardcoding it
            year_total = math.ceil(
                bill_plan.price * self.NUMBER_OF_MONTHS_CHARGED_YEARLY) - 0.01

            # reset percentage for plans other that free plan
            yearly_discount_percent = self.YEARLY_PAYMENT_DISCOINT_PERCENT

        user_sub_dict = {
            **bill_plan.to_dict(),
            "yearly_total": year_total,
            "yearly_original": bill_plan.price * 12,
            "yearly_discount_percent": yearly_discount_percent
        }

        return user_sub_dict



billing_plan_service = BillingPlanService()
