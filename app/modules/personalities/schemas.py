"""Pydantic schemas for Personality request/response validation"""

from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime

class PersonalityBase(BaseModel):
    """Base schema for personalities"""
    name: str = Field(..., min_length=1, max_length=255, description="Personality name")
    description: Optional[str] = Field(None, description="Optional description")

class PersonalityCreate(PersonalityBase):
    """Schema for creating a new custom personality"""
    pass

class PersonalityUpdate(BaseModel):
    """Schema for updating an existing custom personality"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None)

class PersonalityResponse(PersonalityBase):
    """Schema for personality response (read-only)"""
    id: UUID
    is_system: bool
    tenant_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Friendly",
                "description": "Warm and welcoming tone",
                "is_custom": False,
                "tenant_id": None,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
            }
        }

class PersonalityListResponse(BaseModel):
    """Schema for personality listing"""
    personalities: list[PersonalityResponse]
    count: int
