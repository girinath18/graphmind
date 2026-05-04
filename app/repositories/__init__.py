"""Repository layer - enforced tenant isolation"""

from .base import BaseRepository, UserRepository

__all__ = ["BaseRepository", "UserRepository"]
