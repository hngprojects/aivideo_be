from pydantic import BaseModel
from datetime import datetime
from typing import List


class CreateBillingPlanSchema(BaseModel):
    plan_name: str
    price: float
    plan_interval: str
    currency: str
    features: List[str]


class CreateBillingPlanReturnData(CreateBillingPlanSchema):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CreateBillingPlanResponse(BaseModel):
    status_code: int = 200
    success: bool
    message: str
    data: CreateBillingPlanReturnData


class GetBillingPlanData(BaseModel):
    billing_plans: List[CreateBillingPlanReturnData]


class GetBillingPlanListResponse(BaseModel):
    status_code: int = 200
    success: bool
    message: str
    data: GetBillingPlanData
