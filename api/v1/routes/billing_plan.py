from fastapi import Depends, APIRouter, status
from sqlalchemy.orm import Session


from api.v1.schemas.billing_plan import CreateBillingPlanSchema, CreateBillingPlanResponse
from api.v1.services.billing_plan import billing_plan_service as bp_service
from api.utils.success_response import success_response
from api.v1.services.user import user_service
from api.db.database import get_db
from api.v1.models import User


billing_plan = APIRouter(prefix="/billing_plans", tags=["Billing Plan"])


@billing_plan.post("/", response_model=CreateBillingPlanResponse)
async def create_billing_plan(
    billing_plan_schema: CreateBillingPlanSchema,
    current_user: User = Depends(user_service.get_current_super_admin),
    db: Session = Depends(get_db),
):
    """
    Endpoint to create new billing plan
    """

    new_plan = bp_service.create(db=db, schema=billing_plan_schema)

    return success_response(
        status_code=status.HTT,
        message="Billing plan created successfully",
        data=new_plan.to_dict(),
    )