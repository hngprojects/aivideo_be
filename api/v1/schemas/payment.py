from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import List

from api.v1.schemas.billing_plan import CreateBillingPlanResponse
from api.v1.schemas.user_subscription import CreateUserSubResponse


class InitiatePaymentSchema(BaseModel):
    email: EmailStr
    billing_plan_id: str
    payment_gateway: str
    redirect_url: str
    auto_renew: bool = False


class InitiatePaymentData(BaseModel):
    name: str
    price: str
    email: str
    tx_ref: str
    currency: str
    public_key: str
    action_url: str
    redirect_url: str
    payment_title: str
    payment_description: str


class InitiatePaymentResponse(BaseModel):
    status_code: int = 200
    success: bool
    message: str
    payment_url: str


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
