"""Standard response formatting and data transformations"""

from typing import Any, Dict, Optional
from datetime import datetime
from pydantic import BaseModel


class StandardResponse(BaseModel):
    """
    Standard API response format for all endpoints.

    Format:
    {
        "success": bool,          # True if operation succeeded
        "data": any,              # Response data (null if error/empty)
        "error": str | null,      # Error message (null if success)
        "meta": {}                # Metadata: pagination, timing, etc.
    }

    Usage in routes:
        @router.get("/endpoint")
        async def my_endpoint():
            return format_success({"items": [...]}, meta={"total": 100})
    """

    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    meta: Dict[str, Any] = {}


def format_success(
    data: Any = None, meta: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Format a successful response.

    Args:
        data: Response data payload
        meta: Optional metadata (pagination, timing, etc.)

    Returns:
        Standardized success response dict
    """
    return {"success": True, "data": data, "error": None, "meta": meta or {}}


def format_error(
    error_message: str, meta: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Format an error response.

    Args:
        error_message: Human-readable error message
        meta: Optional metadata

    Returns:
        Standardized error response dict
    """
    return {"success": False, "data": None, "error": error_message, "meta": meta or {}}


def format_paginated(
    items: list, total: int, skip: int = 0, limit: int = 20
) -> Dict[str, Any]:
    """
    Format a paginated response.

    Args:
        items: List of items
        total: Total count across all pages
        skip: Offset (default: 0)
        limit: Page size (default: 20)

    Returns:
        Paginated response format
    """
    pages = (total + limit - 1) // limit if limit > 0 else 1
    current_page = (skip // limit) + 1 if limit > 0 else 1

    return format_success(
        data=items,
        meta={
            "pagination": {
                "total": total,
                "page": current_page,
                "pages": pages,
                "limit": limit,
                "skip": skip,
            }
        },
    )


def format_datetime(
    dt: Optional[datetime], fmt: str = "%Y-%m-%d %H:%M:%S"
) -> Optional[str]:
    """
    Format datetime to string.

    Args:
        dt: Datetime object
        fmt: Format string

    Returns:
        Formatted datetime string or None
    """
    return dt.strftime(fmt) if dt else None


def camel_to_snake(name: str) -> str:
    """Convert camelCase to snake_case"""
    import re

    name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()


def snake_to_camel(name: str) -> str:
    """Convert snake_case to camelCase"""
    components = name.split("_")
    return components[0] + "".join(x.title() for x in components[1:])
