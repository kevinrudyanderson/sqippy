from typing import Optional

from fastapi import HTTPException, status

from app.auth.models import User
from app.auth.roles import UserRole


def can_manage_queue(user: Optional[User]) -> bool:
    """Check if user can create, update, or delete queues"""
    if not user:
        return False
    return user.role in [UserRole.STAFF, UserRole.ADMIN, UserRole.SUPER_ADMIN]


def can_manage_customers(user: Optional[User]) -> bool:
    """Check if user can call next customer, complete, or cancel customers"""
    if not user:
        return False
    return user.role in [UserRole.STAFF, UserRole.ADMIN, UserRole.SUPER_ADMIN]


def can_view_queue_details(user: Optional[User]) -> bool:
    """Check if user can view detailed queue information"""
    if not user:
        return False
    return user.role in [UserRole.STAFF, UserRole.ADMIN, UserRole.SUPER_ADMIN]


def can_add_customer_to_queue(user: Optional[User]) -> bool:
    """Check if user can add customers to queue (all authenticated users can)"""
    return True  # Anyone can add customers to queue


def can_cancel_own_queue_entry(
    user: Optional[User], queue_customer_user_id: Optional[str]
) -> bool:
    """Check if user can cancel their own queue entry"""
    if not user or not queue_customer_user_id:
        return False
    return user.user_id == queue_customer_user_id


def require_queue_management_permission(user: Optional[User]) -> User:
    """Require queue management permission, raise HTTPException if not authorized"""
    if not can_manage_queue(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Queue management permission required",
        )
    return user


def require_customer_management_permission(user: Optional[User]) -> User:
    """Require customer management permission, raise HTTPException if not authorized"""
    if not can_manage_customers(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customer management permission required",
        )
    return user
