from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.auth.roles import UserRole


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class CustomerSignUp(BaseModel):
    """Simple sign up for customers"""

    name: Optional[str] = Field(default=None)
    email: Optional[EmailStr] = Field(default=None)
    phone_number: Optional[str] = Field(default=None, pattern=r"^\+?[1-9]\d{1,14}$")

    @field_validator("email", "phone_number")
    def validate_email_or_phone_number(cls, v, values):
        if not v and not values.get("email") and not values.get("phone_number"):
            raise ValueError("Either email or phone number must be provided")
        return v


class UserRegistration(BaseModel):
    """Registration for business owners/managers"""
    
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    phone_number: Optional[str] = Field(default=None, pattern=r"^\+?[1-9]\d{1,14}$")
    password: str = Field(min_length=8)
    
    # Business/location info (optional, can be added later)
    business_name: Optional[str] = Field(default=None, max_length=200)
    business_type: Optional[str] = Field(default=None, max_length=100)


class StaffLogin(BaseModel):
    """Login for staff"""

    email: EmailStr
    password: str = Field(min_length=8)


class StaffCreate(BaseModel):
    """Create a new staff user"""

    name: str

    email: EmailStr
    phone_number: Optional[str] = Field(default=None, pattern=r"^\+?[1-9]\d{1,14}$")
    password: str = Field(min_length=8)

    role: UserRole = Field(..., description="Must be Staff or Admin")

    @field_validator("role")
    def validate_role(cls, v):
        if v == UserRole.CUSTOMER:
            raise ValueError("Cannot create customer users with passwords")
        return v


class UserResponse(BaseModel):
    user_id: UUID
    name: str
    email: EmailStr
    phone_number: Optional[str] = Field(default=None, pattern=r"^\+?[1-9]\d{1,14}$")
    role: UserRole
    is_active: bool

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class UserUpdate(BaseModel):
    name: Optional[str] = Field(default=None)
    email: Optional[EmailStr] = Field(default=None)
    phone_number: Optional[str] = Field(
        default=None, pattern_grammar=r"^\+?[1-9]\d{1,14}$"
    )
    role: Optional[UserRole] = Field(default=None)
