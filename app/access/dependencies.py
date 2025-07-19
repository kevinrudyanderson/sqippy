from typing import Optional

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.access.models import AccessLevel
from app.access.repository import UserLocationAccessRepository
from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.auth.roles import UserRole
from app.database import get_db


def get_access_repository(
    db: Session = Depends(get_db),
) -> UserLocationAccessRepository:
    return UserLocationAccessRepository(db)


def require_location_access(
    location_id: str, min_access_level: AccessLevel = AccessLevel.VIEWER
):
    """Factory function to create location access dependency"""

    def _check_access(
        current_user: User = Depends(get_current_user),
        access_repo: UserLocationAccessRepository = Depends(get_access_repository),
    ) -> User:
        """Require user to have minimum access level to a location"""
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
            )

        # Super admins can access everything
        if current_user.role == UserRole.SUPER_ADMIN:
            return current_user

        # Check user's access to the location
        if not access_repo.check_access(
            current_user.user_id, location_id, min_access_level
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient access to location. Required: {min_access_level.value}",
            )

        return current_user

    return _check_access


def require_location_ownership(location_id: str):
    """Require user to be owner of a location"""
    return require_location_access(location_id, AccessLevel.OWNER)


def require_location_management(location_id: str):
    """Require user to have management access to a location"""
    return require_location_access(location_id, AccessLevel.MANAGER)


def get_user_accessible_locations(
    current_user: User = Depends(get_current_user),
    access_repo: UserLocationAccessRepository = Depends(get_access_repository),
) -> list:
    """Get list of location IDs the current user has access to"""
    if not current_user:
        return []

    # Super admins can access everything - return empty list to indicate "all"
    if current_user.role == UserRole.SUPER_ADMIN:
        return []  # Empty list means no filtering needed

    # Get user's accessible locations
    access_records = access_repo.get_user_accessible_locations(current_user.user_id)
    return [access.location_id for access in access_records]


class UserContext:
    """Context object containing current user and their accessible locations"""

    def __init__(self, user: User, accessible_location_ids: list):
        self.user = user
        self.accessible_location_ids = accessible_location_ids
        self.is_super_admin = user.role == UserRole.SUPER_ADMIN if user else False

    def has_access_to_location(
        self, location_id: str, min_access_level: AccessLevel = AccessLevel.VIEWER
    ) -> bool:
        """Check if user has access to a specific location"""
        if self.is_super_admin:
            return True
        return location_id in self.accessible_location_ids

    def can_access_all(self) -> bool:
        """Check if user can access all resources (super admin)"""
        return self.is_super_admin


def get_user_context(
    current_user: User = Depends(get_current_user),
    accessible_locations: list = Depends(get_user_accessible_locations),
) -> UserContext:
    """Get user context with access information"""
    return UserContext(current_user, accessible_locations)
