"""Users schemas (Pydantic models)"""
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserResponse(BaseModel):
    """User response schema"""
    id: str
    email: EmailStr
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: bool
    role: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """User update schema"""
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[str] = None
