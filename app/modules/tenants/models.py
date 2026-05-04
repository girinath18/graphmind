"""Tenants database models"""
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class Tenant(Base):
    """Tenant model for multi-tenant support"""
    __tablename__ = "tenants"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    slug = Column(String, unique=True, index=True)
    owner_id = Column(String, ForeignKey("users.id"))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
