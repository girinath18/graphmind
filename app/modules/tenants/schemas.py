"""Tenants schemas (Pydantic models)"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class TenantCreate(BaseModel):
    """Tenant creation schema"""
    name: str
    slug: str


class TenantUpdate(BaseModel):
    """Tenant update schema"""
    name: Optional[str] = None
    slug: Optional[str] = None
    is_active: Optional[bool] = None


class TenantResponse(BaseModel):
    """Tenant response schema"""
    id: str
    name: str
    slug: str
    owner_id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
