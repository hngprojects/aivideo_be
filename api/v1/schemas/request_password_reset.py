from pydantic import BaseModel, EmailStr, Field, field_validator
import re


class RequestEmail(BaseModel):
    user_email: EmailStr


class ResetPassword(BaseModel):
    new_password: str = Field(min_length=3)
    confirm_password: str = Field(min_length=3)