from typing import Optional

from fastapi import Depends, HTTPException, status

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.auth.roles import UserRole


def can_manage_location(user: Optional[User]) -> bool:
    """Check if user can create, update, or delete locations"""
    if not user:
        return False
    return user.role in [UserRole.STAFF, UserRole.ADMIN, UserRole.SUPER_ADMIN]


def require_location_management_permission(
    current_user: Optional[User] = Depends(get_current_user),
) -> User:
    """Require user to have location management permission"""
    if not can_manage_location(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
        )
    return current_user
