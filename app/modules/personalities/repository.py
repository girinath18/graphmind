"""Repository layer for Personality (PostgreSQL)"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, delete, func
from typing import Optional, List
import logging
import uuid

from .models import Personality
from ...core.base_repository import BaseRepository

logger = logging.getLogger(__name__)

class PersonalityRepository(BaseRepository):
    """
    Repository for Personality CRUD operations.
    
    Supports:
    - Listing system personalities (is_system=True)
    - Listing tenant personalities (is_system=False, tenant_id=X)
    - Creating/Updating custom personalities
    """

    def __init__(self, db: AsyncSession, tenant_id: str, user_id: Optional[str] = None):
        super().__init__(db, tenant_id)
        self.user_id = uuid.UUID(user_id) if user_id else None
        self.model = Personality

    async def create(
        self,
        name: str,
        description: Optional[str] = None,
        is_system: bool = False,
    ) -> Personality:
        """Create a new personality"""
        personality = Personality(
            id=uuid.uuid4(),
            name=name,
            description=description,
            is_system=is_system,
            is_active=True,
            tenant_id=self.tenant_id if not is_system else None,
            user_id=self.user_id if not is_system else None
        )
        self.db.add(personality)
        await self.db.flush()
        return personality

    async def get_by_id(self, personality_id: str) -> Optional[Personality]:
        """
        Get personality by ID.
        Personalities are visible if they are system-wide OR belong to the tenant.
        """
        result = await self.db.execute(
            select(Personality).where(
                and_(
                    Personality.id == uuid.UUID(personality_id),
                    or_(
                        Personality.is_system == True,
                        Personality.tenant_id == self.tenant_id
                    )
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_personalities(self) -> List[Personality]:
        """
        List all available personalities for the tenant:
        - System personalities (is_system=True)
        - Tenant specific personalities (is_system=False AND tenant_id=tenant_id)
        """
        result = await self.db.execute(
            select(Personality).where(
                or_(
                    Personality.is_system == True,
                    Personality.tenant_id == self.tenant_id
                )
            ).order_by(Personality.is_system.desc(), Personality.name.asc())
        )
        return result.scalars().all()

    async def update(self, personality_id: str, **kwargs) -> Optional[Personality]:
        """
        Update custom personality. System personalities cannot be updated via this path.
        """
        personality = await self.db.get(Personality, uuid.UUID(personality_id))
        
        if not personality:
            return None
            
        if personality.is_system or personality.tenant_id != self.tenant_id:
            logger.warning(f"Unauthorized update attempt for personality {personality_id}")
            return None

        for field, value in kwargs.items():
            if hasattr(personality, field) and value is not None:
                setattr(personality, field, value)
        
        await self.db.flush()
        return personality

    async def delete(self, personality_id: str) -> bool:
        """
        Delete custom personality.
        """
        personality = await self.db.get(Personality, uuid.UUID(personality_id))
        
        if not personality:
            return False
            
        if personality.is_system or personality.tenant_id != self.tenant_id:
            logger.warning(f"Unauthorized delete attempt for personality {personality_id}")
            return False

        await self.db.delete(personality)
        await self.db.flush()
        return True

    async def get_by_name(self, name: str) -> Optional[Personality]:
        """Check if personality with same name exists for this tenant or system-wide"""
        result = await self.db.execute(
            select(Personality).where(
                and_(
                    Personality.name == name,
                    or_(
                        Personality.is_system == True,
                        Personality.tenant_id == self.tenant_id
                    )
                )
            )
        )
        return result.scalar_one_or_none()
