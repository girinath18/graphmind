"""Pagination schemas"""
from pydantic import BaseModel
from typing import TypeVar, Generic, List

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Pagination parameters"""
    skip: int = 0
    limit: int = 20


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper"""
    items: List[T]
    total: int
    skip: int
    limit: int
    
    @property
    def total_pages(self) -> int:
        """Calculate total pages"""
        if self.limit == 0:
            return 0
        return (self.total + self.limit - 1) // self.limit
