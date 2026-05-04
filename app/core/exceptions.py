"""Custom exceptions for the application"""
from fastapi import HTTPException, status


class TenantNotFoundError(HTTPException):
    """Raised when tenant is not found"""
    def __init__(self, tenant_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant '{tenant_id}' not found"
        )


class UnauthorizedError(HTTPException):
    """Raised when user is not authorized"""
    def __init__(self, detail: str = "Not authenticated"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )


class ForbiddenError(HTTPException):
    """Raised when user lacks permission"""
    def __init__(self, detail: str = "Access forbidden"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


class ValidationError(HTTPException):
    """Raised on validation errors"""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail
        )
