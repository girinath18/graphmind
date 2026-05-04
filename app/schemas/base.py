"""Base Pydantic models"""
from pydantic import BaseModel
from datetime import datetime


class BaseSchema(BaseModel):
    """Base schema with common fields"""
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    """Standard message response"""
    message: str
    status: str = "success"
