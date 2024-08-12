from pydantic import BaseModel
from datetime import datetime
from typing import List

from api.v1.schemas.billing_plan import CreateBillingPlanResponse
from api.v1.schemas.user_subscription import CreateUserSubResponse


class PaymentBase(BaseModel):
    amount: float
    currency: str
    status: str
    method: str


class CreatePaymentSchema(PaymentBase):
    user_id: str
    transaction_id: str


class CreatePaymentReturnData(CreatePaymentSchema):
    id: str
    created_at: datetime
    updated_at: datetime


class PaymentAndPlanAndSubcription(BaseModel):
    payment: CreatePaymentReturnData
    billing_plan: CreateBillingPlanResponse
    user_subscription: CreateUserSubResponse


class CreatePaymentResponse(BaseModel):
    status_code: int = 200
    success: bool
    message: str
    data: PaymentAndPlanAndSubcription

    class Config:
        from_attributes = True


class PaymentsData(BaseModel):
    current_page: int
    total_pages: int
    limit: int
    total_items: int
    payments: List[CreatePaymentSchema]
