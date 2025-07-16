import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import HTTPException, status
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext

from app.auth.models import User
from app.auth.repository import UserRepository
from app.auth.schemas import StaffCreate, TokenResponse

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
        self.secret_key = os.getenv("SECRET_KEY")
        self.algorithm = os.getenv("ALGORITHM")
        self.access_token_expire_minutes = int(
            os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30)
        )
        self.refresh_token_expire_days = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 30))

    def hash_password(self, password: str) -> str:
        return password_context.hash(password)

    def verify_password(self, password: str, hashed_password: str) -> bool:
        return password_context.verify(password, hashed_password)

    def create_access_token(
        self, user: User, expires_delta: Optional[timedelta] = None
    ) -> str:
        to_encode = {
            "sub": str(user.email),
            "role": user.role.value,
        }

        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=self.access_token_expire_minutes
            )

        to_encode.update({"exp": expire, "type": "access"})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(self) -> str:
        return secrets.token_urlsafe(32)

    def authenticate_staff(self, email: str, password: str) -> User:
        user = self.user_repository.get_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )
        if not self.verify_password(password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )

        access_token = self.create_access_token(user)

        return TokenResponse(
            access_token=access_token,
            expires_in=self.access_token_expire_minutes,
        )

    def create_staff_user(self, staff_create: StaffCreate) -> User:
        existing_user = self.user_repository.get_by_email(staff_create.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        staff_create.password = self.hash_password(staff_create.password)
        user = self.user_repository.create_staff_user(staff_create)
        return user
