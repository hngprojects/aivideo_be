from fastapi import Depends, APIRouter, status
from sqlalchemy.orm import Session


from api.v1.schemas.billing_plan import (
    CreateBillingPlanSchema, CreateBillingPlanResponse, GetBillingPlanListResponse
)
from api.v1.services.billing_plan import billing_plan_service as bp_service
from api.utils.success_response import success_response
from api.v1.services.user import user_service
from api.db.database import get_db
from api.v1.models import User


billing_plan = APIRouter(prefix="/billing-plans", tags=["Billing Plan"])


@billing_plan.post("", response_model=CreateBillingPlanResponse)
async def create_billing_plan(
    billing_plan_schema: CreateBillingPlanSchema,
    current_user: User = Depends(user_service.get_current_super_admin),
    db: Session = Depends(get_db),
):
    """
    Endpoint to create new billing plan by a `superadmin`
    """

    new_plan = bp_service.create(db=db, schema=billing_plan_schema)

    return success_response(
        status_code=status.HTTP_201_CREATED,
        message="Billing plan created successfully.",
        data=new_plan.to_dict(),
    )


@billing_plan.get("", response_model=GetBillingPlanListResponse)
async def get_all_billing_plans(
    _: User = Depends(user_service.get_current_user),
    db: Session = Depends(get_db),
):
    """
    Endpoint to get all billing plans.
    """

    all_plans = bp_service.fetch_all(db=db)

    return success_response(
        status_code=status.HTTP_200_OK,
        message="Billing plans fetched successfully.",
        data={"billing_plans": [bp.to_dict() for bp in all_plans]},
    )