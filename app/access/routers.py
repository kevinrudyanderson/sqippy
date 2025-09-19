from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.access.dependencies import get_access_repository
from app.access.models import AccessLevel, UserLocationAccess
from app.access.repository import UserLocationAccessRepository
from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.database import get_db


class GrantAccessRequest(BaseModel):
    user_email: str
    location_id: UUID
    access_level: AccessLevel


class AccessResponse(BaseModel):
    access_id: UUID
    user_id: UUID
    location_id: UUID
    access_level: AccessLevel
    granted_by: UUID
    granted_at: str
    is_active: bool

    class Config:
        from_attributes = True


router = APIRouter(prefix="/access", tags=["access"])


@router.post("/grant", response_model=AccessResponse)
def grant_location_access(
    grant_request: GrantAccessRequest,
    current_user: User = Depends(get_current_user),
    access_repo: UserLocationAccessRepository = Depends(get_access_repository),
    db: Session = Depends(get_db),
):
    """Grant access to a location (only owners can grant access)"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )

    # Check if current user is owner of the location
    if not access_repo.can_grant_access(
        current_user.user_id, grant_request.location_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only location owners can grant access",
        )

    # Find the target user by email
    from app.auth.repository import UserRepository

    user_repo = UserRepository(db)
    target_user = user_repo.get_by_email(grant_request.user_email)

    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Grant access
    access_record = access_repo.grant_access(
        user_id=target_user.user_id,
        location_id=grant_request.location_id,
        access_level=grant_request.access_level,
        granted_by=current_user.user_id,
    )

    return AccessResponse.model_validate(access_record)


@router.get("/my-locations", response_model=List[AccessResponse])
def get_my_location_access(
    current_user: User = Depends(get_current_user),
    access_repo: UserLocationAccessRepository = Depends(get_access_repository),
):
    """Get all locations the current user has access to"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )

    access_records = access_repo.get_user_accessible_locations(current_user.user_id)
    return [AccessResponse.model_validate(record) for record in access_records]


@router.delete("/revoke/{user_id}/{location_id}")
def revoke_location_access(
    user_id: str,
    location_id: str,
    current_user: User = Depends(get_current_user),
    access_repo: UserLocationAccessRepository = Depends(get_access_repository),
):
    """Revoke a user's access to a location (only owners can revoke)"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )

    # Check if current user is owner of the location
    if not access_repo.can_grant_access(current_user.user_id, location_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only location owners can revoke access",
        )

    # Can't revoke your own access
    if user_id == current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot revoke your own access",
        )

    success = access_repo.revoke_access(user_id, location_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Access record not found"
        )

    return {"message": "Access revoked successfully"}
