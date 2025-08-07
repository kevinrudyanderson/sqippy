from fastapi import APIRouter, Depends, status

from app.auth.dependencies import require_authenticated_user
from app.auth.models import User
from app.users.dependencies import get_user_service
from app.users.schemas import (
    UserProfileResponse,
    UserProfileUpdate,
    ChangePasswordRequest,
)
from app.users.service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/profile", response_model=UserProfileResponse)
async def get_my_profile(
    current_user: User = Depends(require_authenticated_user),
    user_service: UserService = Depends(get_user_service),
):
    """Get current user's profile"""
    user = user_service.get_user_profile(current_user.user_id)
    return UserProfileResponse(**user.__dict__)


@router.patch("/profile", response_model=UserProfileResponse)
async def update_my_profile(
    profile_update: UserProfileUpdate,
    current_user: User = Depends(require_authenticated_user),
    user_service: UserService = Depends(get_user_service),
):
    """Update current user's profile"""
    user = user_service.update_user_profile(current_user.user_id, profile_update)
    return UserProfileResponse(**user.__dict__)


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    password_request: ChangePasswordRequest,
    current_user: User = Depends(require_authenticated_user),
    user_service: UserService = Depends(get_user_service),
):
    """Change current user's password"""
    user_service.change_password(current_user.user_id, password_request)


@router.delete("/account", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_my_account(
    current_user: User = Depends(require_authenticated_user),
    user_service: UserService = Depends(get_user_service),
):
    """Deactivate current user's account"""
    user_service.deactivate_account(current_user.user_id)