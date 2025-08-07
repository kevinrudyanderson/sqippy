import os
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth.models import User
from app.auth.repository import UserRepository
from app.auth.roles import UserRole
from app.auth.service import AuthService
from app.database import get_db

security = HTTPBearer(auto_error=False)


def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    user_repository: UserRepository = Depends(get_user_repository),
) -> Optional[User]:
    if not credentials:
        return None

    try:
        token = credentials.credentials
        payload = jwt.decode(
            token, os.getenv("SECRET_KEY"), algorithms=[os.getenv("ALGORITHM")]
        )
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )

        user = user_repository.get_by_email(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="User account is inactive"
            )
        return user

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )


async def require_staff_or_admin(
    current_user: Optional[User] = Depends(get_current_user),
) -> User:

    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized"
        )

    if current_user.role not in [
        UserRole.STAFF,
        UserRole.ADMIN,
        UserRole.SUPER_ADMIN,
    ]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    return current_user


async def require_authenticated_user(
    current_user: Optional[User] = Depends(get_current_user),
) -> User:
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )
    return current_user


async def require_admin(
    current_user: Optional[User] = Depends(get_current_user),
) -> User:

    if not current_user or current_user.role not in [
        UserRole.ADMIN,
        UserRole.SUPER_ADMIN,
    ]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )

    return current_user
