from pydantic import BaseModel, Field, EmailStr,  validator
from fastapi import UploadFile, Form
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
    social: Optional[str] = None
    bio: Optional[str] = Field(None)
    phone_number: Optional[str] = Field(None)
    
    class Config:
        extra = 'allow'



class ProfileCreateUpdate(BaseModel):
    '''Schema to create or update a profile'''
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    pronouns: Optional[str] = Field(None, max_length=50)
    job_title: Optional[str] = Field(None, max_length=100)
    social: Optional[str] = None
    bio: Optional[str] = Field(None)
    phone_number: Optional[str] = Field(None)
    email: Optional[EmailStr] = None
    avatar_url: Optional[str] = None
    avatar: Optional[UploadFile] = None
    
    # Validator for phone number
    @validator('phone_number')
    def phone_validator(cls, value):
        # Ensure phone number contains only digits and may start with '+'
        if not re.fullmatch(r"^\+?[0-9]+$", value):
            raise ValueError("Phone number must contain only digits and may start with '+'.")
        
        # Validate length of phone number
        number_length = len(re.sub(r"\D", "", value))  
        if number_length < 10 or number_length > 15:
            raise ValueError("Phone number must be between 10 and 15 digits long.")
        
        return value


    
    class Config:
        extra = 'allow'
        
        
class ProfileUpdateForm(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    pronouns: Optional[str] = Field(None, max_length=50)
    job_title: Optional[str] = Field(None, max_length=100)
    social: Optional[str] = None
    bio: Optional[str] = Field(None)
    social: Optional[str] = None
    phone_number: Optional[str] = Field(None, pattern=r'^\+?[1-9]\d{1,14}$')
    email: Optional[EmailStr] = None
    avatar_url: Optional[str] = None
    
    
    @classmethod
    def as_form(
        cls,
        username: Optional[str] = Form(None),
        pronouns: Optional[str] = Form(None),
        job_title: Optional[str] = Form(None),
        social: Optional[str] = Form(None),
        bio: Optional[str] = Form(None),
        phone_number: Optional[str] = Form(None),
        email: Optional[str] = Form(None),
        avatar_url: Optional[str] = Form(None),
    ) -> "ProfileUpdateForm":
        return cls(
            username=username,
            pronouns=pronouns,
            job_title=job_title,
            social=social,
            bio=bio,
            phone_number=phone_number,
            email=email,
            avatar_url=avatar_url,
        )

