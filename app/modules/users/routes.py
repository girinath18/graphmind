"""Users management routes"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from ..auth.dependencies import get_current_user
from ...core.database import get_db
from . import services, schemas

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/{user_id}", response_model=schemas.UserResponse)
async def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    """Get user by ID"""
    return await services.get_user(user_id, db)


@router.get("/", response_model=list[schemas.UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    """List all users"""
    return await services.list_users(skip, limit, db)


@router.put("/{user_id}", response_model=schemas.UserResponse)
async def update_user(
    user_id: str,
    user_update: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    """Update user"""
    return await services.update_user(user_id, user_update, db)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    """Delete user"""
    return await services.delete_user(user_id, db)
