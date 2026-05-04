"""Service layer for Personality (business logic + transactions)"""

from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
import logging
import uuid

from .repository import PersonalityRepository
from . import schemas
from ...utils.formatters import format_success, format_error

logger = logging.getLogger(__name__)

class PersonalityService:
    """
    Personality service - manages agent personalities.
    """

    def __init__(self, db: AsyncSession, tenant_id: str, user_id: Optional[str] = None):
        self.db = db
        self.tenant_id = uuid.UUID(tenant_id)
        self.user_id = uuid.UUID(user_id) if user_id else None
        self.repository = PersonalityRepository(db, str(self.tenant_id), str(self.user_id) if self.user_id else None)

    async def create_personality(self, request: schemas.PersonalityCreate) -> dict:
        """Create a new custom personality for the tenant"""
        try:
            # Check for duplicates
            existing = await self.repository.get_by_name(request.name)
            if existing:
                return format_error(
                    f"Personality with name '{request.name}' already exists.",
                    meta={"status_code": 400}
                )

            personality = await self.repository.create(
                name=request.name,
                description=request.description,
                is_system=False
            )
            await self.db.commit()
            
            return format_success(
                {
                    "personality": schemas.PersonalityResponse.model_validate(
                        personality, from_attributes=True
                    )
                },
                meta={"message": "Personality created successfully"}
            )
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create personality: {e}")
            return format_error(f"Failed to create personality: {str(e)}")

    async def get_personality(self, personality_id: str) -> dict:
        """Get personality by ID"""
        try:
            personality = await self.repository.get_by_id(personality_id)
            if not personality:
                return format_error("Personality not found", meta={"status_code": 404})

            return format_success(
                {
                    "personality": schemas.PersonalityResponse.model_validate(
                        personality, from_attributes=True
                    )
                }
            )
        except Exception as e:
            logger.error(f"Failed to get personality: {e}")
            return format_error(f"Failed to retrieve personality: {str(e)}")

    async def list_personalities(self) -> dict:
        """List all available personalities for the tenant"""
        try:
            personalities = await self.repository.list_personalities()
            return format_success(
                {
                    "personalities": [
                        schemas.PersonalityResponse.model_validate(p, from_attributes=True)
                        for p in personalities
                    ],
                    "count": len(personalities)
                }
            )
        except Exception as e:
            logger.error(f"Failed to list personalities: {e}")
            return format_error(f"Failed to list personalities: {str(e)}")

    async def update_personality(self, personality_id: str, request: schemas.PersonalityUpdate) -> dict:
        """Update custom personality"""
        try:
            update_data = request.model_dump(exclude_none=True)
            if not update_data:
                return format_error("No fields provided for update", meta={"status_code": 400})

            personality = await self.repository.update(personality_id, **update_data)
            if not personality:
                return format_error(
                    "Personality not found or is a system personality (cannot update)",
                    meta={"status_code": 404}
                )

            await self.db.commit()
            await self.db.refresh(personality)

            return format_success(
                {
                    "personality": schemas.PersonalityResponse.model_validate(
                        personality, from_attributes=True
                    )
                },
                meta={"message": "Personality updated successfully"}
            )
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to update personality: {e}")
            return format_error(f"Failed to update personality: {str(e)}")

    async def delete_personality(self, personality_id: str) -> dict:
        """Delete custom personality"""
        from ..agents.models import Agent
        from sqlalchemy import select

        try:
            # Check if personality is in use
            result = await self.db.execute(
                select(Agent).where(Agent.personality_id == uuid.UUID(personality_id))
            )
            if result.scalars().first():
                return format_error(
                    "Cannot delete personality because it is linked to one or more agents.",
                    meta={"status_code": 400}
                )

            deleted = await self.repository.delete(personality_id)
            if not deleted:
                return format_error(
                    "Personality not found or is a system personality (cannot delete)",
                    meta={"status_code": 404}
                )

            await self.db.commit()
            return format_success({"id": personality_id}, meta={"message": "Personality deleted successfully"})
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to delete personality: {e}")
            return format_error(f"Failed to delete personality: {str(e)}")
