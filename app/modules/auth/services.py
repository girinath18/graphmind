"""Authentication service - business logic for auth operations"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
import logging
from datetime import timedelta

from ...core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
)
from ...core.config import get_settings
from ...utils.formatters import format_error
from .models import User, Tenant, APIKey
from . import schemas

logger = logging.getLogger(__name__)
settings = get_settings()


async def register_user(request: schemas.RegisterRequest, db: AsyncSession) -> dict:
    """
    Register a new user and optionally create tenant.

    CRITICAL: Must create both Tenant and User in same transaction.
    If tenant_name provided → create new tenant
    If not provided → user chooses existing tenant (not implemented yet)

    Args:
        request: RegisterRequest with email, password, names
        db: Database session

    Returns:
        Dict with user, tenant, tokens
    """
    logger.info(f"📝 Signup attempt: {request.email}")
    try:
        # ============= CREATE TENANT =============
        if request.tenant_name:
            # Check if tenant already exists
            logger.debug(f"  Checking if tenant '{request.tenant_name}' exists...")
            existing_tenant = await db.execute(
                select(Tenant).where(Tenant.name == request.tenant_name)
            )
            if existing_tenant.scalar_one_or_none():
                logger.warning(f"  ❌ Tenant '{request.tenant_name}' already exists")
                return {
                    "success": False,
                    "error": f"Tenant '{request.tenant_name}' already exists",
                }

            # Create new tenant
            tenant_id = uuid.uuid4()
            tenant = Tenant(
                id=tenant_id,
                name=request.tenant_name,
                slug=request.tenant_name.lower().replace(" ", "-"),
            )
            db.add(tenant)
            logger.info(f"  ✅ Created tenant: {tenant.id} ({request.tenant_name})")
        else:
            # For now, require tenant_name
            logger.warning(f"  ❌ No tenant_name provided for signup")
            return {"success": False, "error": "tenant_name required for registration"}

        # ============= CREATE USER =============
        logger.debug(f"  Creating user: {request.email}...")
        user_id = uuid.uuid4()
        hashed_pwd = hash_password(request.password)

        user = User(
            id=user_id,
            tenant_id=tenant_id,
            email=request.email,
            first_name=request.first_name,
            last_name=request.last_name,
            hashed_password=hashed_pwd,
            is_active=True,
        )
        db.add(user)

        # ============= COMMIT TRANSACTION =============
        await db.flush()  # Get IDs before commit
        await db.commit()

        logger.info(f"  ✅ User registered: {user.id}")

        # ============= CREATE TOKENS =============
        logger.debug(f"  Generating tokens...")
        access_token = create_access_token(
            user_id=str(user_id), tenant_id=str(tenant_id)
        )
        refresh_token = create_refresh_token(
            user_id=str(user_id), tenant_id=str(tenant_id)
        )

        logger.info(f"✅ Signup successful: {request.email}")

        return {
            "success": True,
            "user": user,
            "tenant": tenant,
            "tokens": {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": settings.access_token_expire_minutes * 60,
            },
        }

    except Exception as e:
        await db.rollback()
        logger.error(f"Registration error: {e}")
        return {"success": False, "error": f"Registration failed: {str(e)}"}


async def login_user(request: schemas.LoginRequest, db: AsyncSession) -> dict:
    """
    Authenticate user and return tokens.

    Args:
        request: LoginRequest with email and password
        db: Database session

    Returns:
        Dict with user, tenant, tokens
    """
    logger.info(f"🔓 Login attempt: {request.email}")

    # ============= FIND USER =============
    logger.debug(f"  Looking up user: {request.email}...")
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()

    if not user:
        logger.warning(f"  ❌ Login failed: user {request.email} not found")
        return {"success": False, "error": "Invalid email or password"}

    # ============= VERIFY PASSWORD =============
    logger.debug(f"  Verifying password...")
    if not verify_password(request.password, user.hashed_password):
        logger.warning(f"  ❌ Login failed: wrong password for {request.email}")
        return {"success": False, "error": "Invalid email or password"}

    if not user.is_active:
        logger.warning(f"  ❌ Login failed: user {request.email} inactive")
        return {"success": False, "error": "User account is inactive"}

    logger.debug(f"  ✅ Password verified for {request.email}")

    # ============= FETCH TENANT =============
    logger.debug(f"  Fetching tenant: {user.tenant_id}...")
    tenant_result = await db.execute(select(Tenant).where(Tenant.id == user.tenant_id))
    tenant = tenant_result.scalar_one_or_none()

    if not tenant or not tenant.is_active:
        logger.warning(f"  ❌ Login failed: tenant {user.tenant_id} inactive")
        return {"success": False, "error": "Tenant is inactive"}

    logger.debug(f"  ✅ Tenant verified: {tenant.name}")

    # ============= CREATE TOKENS =============
    logger.debug(f"  Generating tokens...")
    access_token = create_access_token(
        user_id=str(user.id), tenant_id=str(user.tenant_id)
    )
    refresh_token = create_refresh_token(
        user_id=str(user.id), tenant_id=str(user.tenant_id)
    )

    logger.info(f"✅ Login successful: {request.email} in tenant: {tenant.name}")

    return {
        "success": True,
        "user": user,
        "tenant": tenant,
        "tokens": {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.access_token_expire_minutes * 60,
        },
    }


async def refresh_access_token(refresh_token: str, db: AsyncSession) -> dict:
    """
    Exchange refresh token for new access token.

    Args:
        refresh_token: Valid refresh token
        db: Database session

    Returns:
        Dict with new tokens
    """
    # ============= VERIFY REFRESH TOKEN =============
    payload = await verify_refresh_token(refresh_token, db)

    if not payload:
        logger.warning("Refresh token invalid or expired")
        return {"success": False, "error": "Invalid or expired refresh token"}

    # ============= VERIFY USER STILL EXISTS =============
    result = await db.execute(select(User).where(User.id == uuid.UUID(payload.user_id)))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        logger.warning(f"Refresh failed: user {payload.user_id} not found or inactive")
        return {"success": False, "error": "User not found or inactive"}

    # ============= CREATE NEW ACCESS TOKEN =============
    access_token = create_access_token(
        user_id=str(user.id), tenant_id=str(user.tenant_id)
    )

    logger.info(f"Refreshed token for user {user.id}")

    return {
        "success": True,
        "tokens": {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.access_token_expire_minutes * 60,
        },
    }
