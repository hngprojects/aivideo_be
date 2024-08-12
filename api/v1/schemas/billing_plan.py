from pydantic import BaseModel
from datetime import datetime
from typing import List


class CreateBillingPlanSchema(BaseModel):
    plan_name: str
    price: float
    plan_interval: str
    currency: str
    features: List[str]


class CreateBillingPlanResponse(CreateBillingPlanSchema):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True