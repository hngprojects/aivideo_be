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
    username: Optional[str] = Field(None, max_length=50)
    pronouns: Optional[str] = Field(None, max_length=50)
    job_title: Optional[str] = Field(None, max_length=100)
    social: Optional[str] = None
    bio: Optional[str] = Field(None)
    phone_number: Optional[str] = Field(None)
    email: Optional[EmailStr] = None
    avatar_url: Optional[str] = None
    avatar: Optional[UploadFile] = None
    
    @validator('phone_number')
    def phone_validator(cls, value):
        if value is None:
            return value
        
        # Ensure phone number contains only digits and may start with '+'
        if not re.fullmatch(r"^\+?[0-9]+$", value):
            raise ValueError("Phone number must contain only digits and may start with '+'.")
        
        # Validate length of phone number
        number_length = len(re.sub(r"\D", "", value))  
        if number_length < 10 or number_length > 15:
            raise ValueError("Phone number must be between 10 and 15 digits long.")
        
        return value

    @validator('job_title', pre=True, always=True)
    def job_title_validator(cls, value):
        if value is None:
            return value 
        
        if not isinstance(value, str):
            raise ValueError("Job title must be a string.")
        
        if not value.replace(" ", "").isalpha():
            raise ValueError("Job title must contain only alphabetic characters.")
        
        return value        
    
    class Config:
        extra = 'allow'
        
        
class ProfileUpdateForm(BaseModel):
    username: Optional[str] = Field(None, max_length=50)
    pronouns: Optional[str] = Field(None, max_length=50)
    job_title: Optional[str] = Field(None, max_length=100)
    social: Optional[str] = None
    bio: Optional[str] = Field(None)
    social: Optional[str] = None
    phone_number: Optional[str] = Field(None, pattern=r'^\+?[1-9]\d{1,14}$')
    email: Optional[EmailStr] = None
    avatar_url: Optional[str] = None
