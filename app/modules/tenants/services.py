"""Tenants business logic"""
from sqlalchemy.orm import Session
from . import models, schemas
import uuid


async def create_tenant(tenant_data: schemas.TenantCreate, owner_id: str, db: Session):
    """Create a new tenant"""
    db_tenant = models.Tenant(
        id=str(uuid.uuid4()),
        name=tenant_data.name,
        slug=tenant_data.slug,
        owner_id=owner_id
    )
    
    db.add(db_tenant)
    db.commit()
    db.refresh(db_tenant)
    return db_tenant


async def get_tenant(tenant_id: str, db: Session):
    """Get tenant by ID"""
    tenant = db.query(models.Tenant).filter(models.Tenant.id == tenant_id).first()
    if not tenant:
        raise ValueError(f"Tenant {tenant_id} not found")
    return tenant


async def list_tenants_for_user(owner_id: str, skip: int, limit: int, db: Session):
    """List tenants for a specific user"""
    return db.query(models.Tenant).filter(
        models.Tenant.owner_id == owner_id
    ).offset(skip).limit(limit).all()


async def update_tenant(tenant_id: str, tenant_update: schemas.TenantUpdate, db: Session):
    """Update tenant"""
    tenant = await get_tenant(tenant_id, db)
    update_data = tenant_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(tenant, field, value)
    
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant


async def delete_tenant(tenant_id: str, db: Session):
    """Delete tenant"""
    tenant = await get_tenant(tenant_id, db)
    db.delete(tenant)
    db.commit()
