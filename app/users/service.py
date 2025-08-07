from fastapi import HTTPException, status
from passlib.context import CryptContext

from app.auth.models import User
from app.auth.repository import UserRepository
from app.users.schemas import UserProfileUpdate, ChangePasswordRequest

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def get_user_profile(self, user_id: str) -> User:
        """Get user profile"""
        user = self.user_repository.get(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user

    def update_user_profile(self, user_id: str, profile_update: UserProfileUpdate) -> User:
        """Update user profile"""
        user = self.user_repository.get(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        updates = profile_update.model_dump(exclude_unset=True)
        
        # Validate email uniqueness
        if "email" in updates and updates["email"] != user.email:
            if self.user_repository.email_exists(updates["email"], user_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already exists"
                )

        # Validate phone uniqueness  
        if "phone_number" in updates and updates["phone_number"] != user.phone_number:
            if self.user_repository.phone_exists(updates["phone_number"], user_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Phone number already exists"
                )

        return self.user_repository.update_profile(user_id, updates)

    def change_password(self, user_id: str, password_request: ChangePasswordRequest) -> User:
        """Change user password"""
        user = self.user_repository.get(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Verify current password
        if not password_context.verify(password_request.current_password, user.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )

        # Hash new password and update
        hashed_password = password_context.hash(password_request.new_password)
        return self.user_repository.update_profile(user_id, {"password": hashed_password})

    def deactivate_account(self, user_id: str) -> User:
        """Deactivate user account"""
        user = self.user_repository.get(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return self.user_repository.update_profile(user_id, {"is_active": False})