from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import List

from api.v1.schemas.base_schema import ResponseBase


class CreateBillingPlanSchema(BaseModel):
    plan_name: str
    price: float
    plan_interval: str
    currency: str
    access_limit: int
    features: List[str]

    @field_validator("plan_interval")
    @classmethod
    def validate_plan_interval(cls, value):
        v = value.lower()
        if v not in ["monthly", "yearly"]:
            raise ValueError("Interval must be either 'monthly' or 'yearly'")
        return v


class CreateBillingPlanReturnData(CreateBillingPlanSchema):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CreateBillingPlanResponse(ResponseBase):
    data: CreateBillingPlanReturnData


class GetBillingPlanData(BaseModel):
    billing_plans: List[CreateBillingPlanReturnData]


class GetBillingPlanListResponse(ResponseBase):
    data: GetBillingPlanData
