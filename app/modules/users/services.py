"""Users business logic"""

from sqlalchemy.orm import Session
from ..auth.models import User
from . import schemas


async def get_user(user_id: str, db: Session):
    """Get user by ID"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError(f"User {user_id} not found")
    return user


async def list_users(skip: int, limit: int, db: Session):
    """List users with pagination"""
    return db.query(User).offset(skip).limit(limit).all()


async def update_user(user_id: str, user_update: schemas.UserUpdate, db: Session):
    """Update user"""
    user = await get_user(user_id, db)
    update_data = user_update.dict(exclude_unset=True)

    for field, value in update_data.items():
        setattr(user, field, value)

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


async def delete_user(user_id: str, db: Session):
    """Delete user"""
    user = await get_user(user_id, db)
    db.delete(user)
    db.commit()
