from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.auth.roles import UserRole
from app.database import get_db
from app.organizations.service import OrganizationService


def require_organization_member(
    current_user: User = Depends(get_current_user),
) -> User:
    """Require user to be authenticated and belong to an organization"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )

    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must belong to an organization",
        )

    return current_user


def require_organization_staff(
    current_user: User = Depends(require_organization_member),
) -> User:
    """Require user to be staff or higher within their organization"""
    if current_user.role not in [UserRole.STAFF, UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Staff privileges required"
        )

    return current_user


def require_organization_admin(
    current_user: User = Depends(require_organization_member),
) -> User:
    """Require user to be admin or higher within their organization"""
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required"
        )

    return current_user


def get_user_organization_id(
    current_user: User = Depends(require_organization_member),
) -> str:
    """Get the current user's organization ID for filtering"""
    return current_user.organization_id


class OrganizationContext:
    """Simple context containing user and their organization"""

    def __init__(self, user: User):
        self.user = user
        self.organization_id = user.organization_id
        self.is_super_admin = user.role == UserRole.SUPER_ADMIN

    def can_access_all_organizations(self) -> bool:
        """Check if user can access all organizations (super admin only)"""
        return self.is_super_admin


def get_organization_context(
    current_user: User = Depends(require_organization_member),
) -> OrganizationContext:
    """Get organization context for the current user"""
    return OrganizationContext(current_user)


def get_organization_service(db: Session = Depends(get_db)) -> OrganizationService:
    """Get organization service dependency"""
    return OrganizationService(db)
