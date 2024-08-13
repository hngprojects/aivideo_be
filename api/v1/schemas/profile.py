from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Dict
import re
from datetime import datetime
from api.v1.schemas.user import UserBase


class ProfileBase(BaseModel):
    '''Base profile schema'''
    id: str
    created_at: datetime
    user: UserBase
    username: Optional[str] = Field(None, max_length=50)
    pronouns: Optional[str] = Field(None, max_length=50)
    job_title: Optional[str] = Field(None, max_length=100)
    social: Optional[Dict[str, str]] = Field(None)
    bio: Optional[str] = Field(None)
    phone_number: Optional[str] = Field(None, pattern=r'^\+?[1-9]\d{1,14}$')
    
    class Config:
        orm_mode = True


class ProfileCreateUpdate(BaseModel):
    '''Schema to create or update a profile'''
    username: Optional[str] = Field(None, max_length=50)
    pronouns: Optional[str] = Field(None, max_length=50)
    job_title: Optional[str] = Field(None, max_length=100)
    social: Optional[Dict[str, str]] = Field(None)
    bio: Optional[str] = Field(None)
    phone_number: Optional[str] = Field(None, pattern=r'^\+?[1-9]\d{1,14}$')
    email: Optional[EmailStr] = None
    avatar_url: Optional[str] = None
    
    class Config:
        orm_mode = True
