from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.auth.roles import UserRole


class UserProfileResponse(BaseModel):
    """User profile information"""

    user_id: UUID
    name: str
    email: EmailStr
    phone_number: Optional[str] = None
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserProfileUpdate(BaseModel):
    """Update user profile information"""

    name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = Field(None, pattern=r"^\+?[1-9]\d{1,14}$")


class ChangePasswordRequest(BaseModel):
    """Change user password"""

    current_password: str = Field(min_length=8)
    new_password: str = Field(min_length=8)


class UserSummary(BaseModel):
    """Summary view of user for listings"""

    user_id: UUID
    name: str
    email: EmailStr
    role: UserRole
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
