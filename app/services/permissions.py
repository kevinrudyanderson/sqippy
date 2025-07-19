from typing import Optional

from fastapi import Depends, HTTPException, status

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.auth.roles import UserRole


def can_manage_services(user: Optional[User]) -> bool:
    """Check if user can create, update, or delete services"""
    if not user:
        return False
    return user.role in [UserRole.STAFF, UserRole.ADMIN, UserRole.SUPER_ADMIN]


def can_view_services(user: Optional[User]) -> bool:
    """Check if user can view services (all authenticated users can)"""
    return user is not None


def require_service_management_permission(
    current_user: Optional[User] = Depends(get_current_user),
) -> User:
    """Require user to have service management permission"""
    if not can_manage_services(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Service management permission required"
        )
    return current_user


def require_authenticated_user(
    current_user: Optional[User] = Depends(get_current_user),
) -> User:
    """Require user to be authenticated"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Authentication required"
        )
    return current_user