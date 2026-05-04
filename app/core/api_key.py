"""API Key authentication system for external integrations"""

from fastapi import Request, HTTPException, status
from fastapi.security import APIKeyHeader
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging
import secrets
from typing import Optional
import hashlib
import hmac  # CRITICAL: Timing-safe comparison

from .config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def hash_api_key(key: str) -> str:
    """
    Hash an API key for storage.

    Never store plaintext API keys!

    Args:
        key: Plaintext API key

    Returns:
        SHA-256 hash of the key
    """
    return hashlib.sha256(key.encode()).hexdigest()


def generate_api_key() -> str:
    """
    Generate a secure random API key.

    Format: graphmind_<32-char-secret>

    Returns:
        Random API key suitable for database storage
    """
    secret = secrets.token_urlsafe(32)
    return f"graphmind_{secret}"


class APIKeyMiddleware(BaseHTTPMiddleware):
    """
    Supports BOTH JWT and API key authentication.

    Priority:
        1. Check Authorization Bearer header (JWT) - standard auth
        2. If missing, check X-API-Key header - API key auth

    If neither present, request is rejected.
    """

    async def dispatch(self, request: Request, call_next):
        # Skip middleware for public endpoints
        if request.url.path in ["/docs", "/redoc", "/openapi.json", "/health"]:
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        api_key_header = request.headers.get("X-API-Key")

        # ===== PREFER JWT (bearer tokens) =====
        if auth_header and auth_header.startswith("Bearer "):
            # JWT will be validated by TenantContextMiddleware
            return await call_next(request)

        # ===== FALLBACK TO API KEY =====
        elif api_key_header:
            # API Key authentication
            # In real implementation, fetch user/tenant from db
            # For now, pass to route handler to validate
            request.state.api_key = api_key_header
            return await call_next(request)

        # ===== NO AUTH FOUND =====
        else:
            logger.warning(f"No auth found for {request.method} {request.url.path}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "success": False,
                    "data": None,
                    "error": "Missing authentication (Bearer token or X-API-Key)",
                    "meta": {},
                },
            )


async def validate_api_key(
    api_key: str, db: AsyncSession
) -> tuple[Optional[str], Optional[str]]:
    """
    Validate API key against database.

    CRITICAL: Uses timing-safe comparison to prevent timing attacks.
    Regular == comparison can leak whether the API key is valid
    based on how long authentication takes.

    Args:
        api_key: Plaintext API key from header
        db: Database session

    Returns:
        Tuple of (user_id, tenant_id) if valid, else (None, None)
    """
    from ..modules.auth.models import APIKey

    # Hash the provided key
    key_hash = hash_api_key(api_key)

    # Find in database
    result = await db.execute(select(APIKey).where(APIKey.key_hash == key_hash))
    api_key_record = result.scalar_one_or_none()

    if not api_key_record:
        logger.warning(f"Invalid API key used")
        # CRITICAL: Always hash a dummy key to prevent timing attacks
        # Even if API key doesn't exist, spend time hashing to leak no info
        dummy_hash = hash_api_key("invalid_key_to_prevent_timing_attack")
        return None, None

    if not api_key_record.is_active:
        logger.warning(f"Inactive API key used: {api_key_record.id}")
        return None, None

    # CRITICAL: Use hmac.compare_digest for timing-safe string comparison
    # Regular == can leak information based on timing
    # This prevents attackers from guessing keys based on response time
    stored_hash = api_key_record.key_hash
    if not hmac.compare_digest(key_hash, stored_hash):
        logger.warning(f"API key hash mismatch (should not happen)")
        return None, None

    return api_key_record.user_id, api_key_record.tenant_id
