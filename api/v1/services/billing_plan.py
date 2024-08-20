from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from uuid_extensions import uuid7
from typing import Any, Optional

from api.v1.schemas.billing_plan import CreateBillingPlanSchema
from api.utils.db_validators import check_model_existence
from api.v1.models.billing_plan import BillingPlan


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


billing_plan_service = BillingPlanService()
