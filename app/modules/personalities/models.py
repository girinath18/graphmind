"""Personality model for defining agent behavior"""

from sqlalchemy import Column, String, Boolean, DateTime, Text, UUID as SQLAlchemyUUID, ForeignKey
from sqlalchemy.sql import func
import uuid
from ...models.base import Base

class Personality(Base):
    """
    Personality model - stored in PostgreSQL.
    
    Personalities define the tone and behavior of an agent.
    System personalities (is_system=True) are available to all tenants.
    Custom personalities (is_system=False) are specific to a tenant.
    """
    __tablename__ = "personalities"

    id = Column(
        SQLAlchemyUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        nullable=False,
    )

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # System vs User/Tenant defined
    is_system = Column(Boolean, default=True, nullable=False)
    
    # Ownership
    tenant_id = Column(
        SQLAlchemyUUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=True, # Null for system personalities
    )
    
    user_id = Column(
        SQLAlchemyUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True, # System personalities don't have a user
    )

    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self) -> str:
        return f"<Personality id={self.id} name={self.name} is_system={self.is_system}>"
