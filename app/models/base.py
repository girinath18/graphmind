"""Base SQLAlchemy model with common fields (tenant_id, timestamps)"""

from sqlalchemy import Column, String, DateTime, UUID
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
import uuid

Base = declarative_base()


class BaseModel(Base):
    """
    Abstract base model for all SQLAlchemy ORM models.

    Provides:
        - id: UUID primary key
        - tenant_id: Multi-tenancy enforcement
        - created_at: Automatic creation timestamp
        - updated_at: Automatic update timestamp

    Every table should inherit from this for consistency.

    Example:
        class User(BaseModel):
            __tablename__ = "users"

            email = Column(String, unique=True, index=True)
            hashed_password = Column(String)
    """

    __abstract__ = True

    # ============= CORE FIELDS =============
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        nullable=False,
    )

    # ============= MULTI-TENANCY =============
    tenant_id = Column(
        UUID(as_uuid=True), nullable=False, index=True  # Fast lookups by tenant
    )

    # ============= TIMESTAMPS =============
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),  # Use PostgreSQL function for precision
        index=True,
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        onupdate=func.now(),
        index=True,
    )

    def __repr__(self) -> str:
        """String representation for debugging"""
        return f"<{self.__class__.__name__} id={self.id} tenant_id={self.tenant_id}>"
