from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import Union


class UserData(BaseModel):
    """
    Schema Response representing the validated google login
    """

    id: str
    first_name: str
    last_name: str
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True


class Tokens(BaseModel):
    """
    Schema representing tokens
    """

    access_token: str
    refresh_token: str
    token_type: str


class StatusResponse(BaseModel):
    """
    Schema Response to the end user
    """

    message: str
    status: str
    statusCode: int
    tokens: Tokens
    user: UserData


class OAuthToken(BaseModel):
    id_token: str


class GoogleUserData(BaseModel):
    """Google Registration schema"""

    id: str
    email: EmailStr
    first_name: str
    last_name: str
    is_active: bool
    created_at: datetime
    last_login: Union[datetime, None]


class GoogleUserResponse(BaseModel):
    status: str
    status_code: int
    message: str
    access_token: str
    id_token: str
    data: GoogleUserData
