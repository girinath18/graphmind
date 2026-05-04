"""Base repository class for all data access layers"""

from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import uuid
import logging

logger = logging.getLogger(__name__)


class BaseRepository:
    """
    Base repository class for all data access patterns.

    CRITICAL:
    - All queries include tenant_id filtering (RLS enforcement)
    - Tenant context must be passed on initialization
    - Cannot circumvent multi-tenancy filtering

    Every repository inherits from this to ensure consistent patterns.
    """

    def __init__(self, db: AsyncSession, tenant_id: str):
        """
        Initialize repository with tenant context.

        Args:
            db: SQLAlchemy AsyncSession
            tenant_id: Tenant UUID (string) for RLS filtering

        CRITICAL: tenant_id is ALWAYS included in queries
        """
        self.db = db
        self.tenant_id = (
            uuid.UUID(tenant_id) if isinstance(tenant_id, str) else tenant_id
        )

        if not self.tenant_id:
            raise ValueError("tenant_id is required for repository initialization")

    async def flush(self):
        """Flush pending changes without commit"""
        await self.db.flush()

    async def commit(self):
        """Commit transaction"""
        await self.db.commit()

    async def rollback(self):
        """Rollback transaction"""
        await self.db.rollback()
