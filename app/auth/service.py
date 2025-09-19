import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import HTTPException, status
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.auth.models import RefreshToken, User
from app.auth.repository import UserRepository
from app.auth.schemas import StaffCreate, TokenResponse
from app.config import settings

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    def __init__(self, user_repository: UserRepository, db_session: Session):
        self.user_repository = user_repository
        self.db_session = db_session
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
        self,
        user: User,
        expires_delta: Optional[timedelta] = timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        ),
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

    def create_refresh_token(self, user: User) -> str:
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=self.refresh_token_expire_days
        )

        # Hash the token with SHA-256 for fast lookups
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        refresh_token = RefreshToken(
            user_id=user.user_id, token=token_hash, expires_at=expires_at
        )

        self.db_session.add(refresh_token)
        self.db_session.commit()

        return token  # Return plain token to client

    def invalidate_refresh_token(self, token: str) -> bool:
        """Invalidate a refresh token by marking it as revoked"""
        # Hash the token for lookup
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        # Direct lookup by hash - O(1) operation
        refresh_token = (
            self.db_session.query(RefreshToken)
            .filter(RefreshToken.token == token_hash, RefreshToken.is_revoked == False)
            .first()
        )

        if refresh_token:
            refresh_token.is_revoked = True
            refresh_token.revoked_at = datetime.now(timezone.utc)
            self.db_session.commit()
            return True

        return False

    def invalidate_all_user_refresh_tokens(self, user_id: str) -> int:
        """Invalidate all refresh tokens for a user (useful for logout all devices)"""
        tokens = (
            self.db_session.query(RefreshToken)
            .filter(RefreshToken.user_id == user_id, RefreshToken.is_revoked == False)
            .all()
        )

        count = 0
        for token in tokens:
            token.is_revoked = True
            token.revoked_at = datetime.now(timezone.utc)
            count += 1

        self.db_session.commit()
        return count

    def is_refresh_token_valid(self, token: str) -> bool:
        """Check if a refresh token is valid (exists, not revoked, not expired)"""
        # Hash the token for lookup
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        # Direct lookup by hash - O(1) operation
        refresh_token = (
            self.db_session.query(RefreshToken)
            .filter(RefreshToken.token == token_hash, RefreshToken.is_revoked == False)
            .first()
        )

        if not refresh_token:
            return False

        # Check expiration
        now = datetime.now()
        now_utc = datetime.now(timezone.utc)
        expires_at = refresh_token.expires_at
        comparison_time = now if expires_at.tzinfo is None else now_utc

        if expires_at < comparison_time:
            # Auto-expire the token
            refresh_token.is_revoked = True
            refresh_token.revoked_at = now if expires_at.tzinfo is None else now_utc
            self.db_session.commit()
            return False

        return True

    def get_user_from_refresh_token(self, token: str) -> Optional[User]:
        """Get user associated with a valid refresh token"""
        if not self.is_refresh_token_valid(token):
            return None

        # Hash the token for lookup
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        # Direct lookup by hash - O(1) operation
        refresh_token = (
            self.db_session.query(RefreshToken)
            .filter(RefreshToken.token == token_hash, RefreshToken.is_revoked == False)
            .first()
        )

        return refresh_token.user if refresh_token else None

    def authenticate_staff(
        self, email: str, password: str
    ) -> tuple[TokenResponse, str]:
        user = self.user_repository.get_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )
        # Ensure only users with passwords can authenticate
        if not user.password:
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
        refresh_token = self.create_refresh_token(user)

        token_response = TokenResponse(
            access_token=access_token,
            expires_in=self.access_token_expire_minutes,
        )

        return token_response, refresh_token

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
