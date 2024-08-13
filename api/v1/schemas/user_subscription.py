from pydantic import BaseModel
from datetime import datetime


class CreateUserSubSchema(BaseModel):
    user_id: str
    billing_plan_id: str
    start_date: datetime
    end_date: datetime


class CreateUserSubResponse(CreateUserSubSchema):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
