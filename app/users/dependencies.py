from fastapi import Depends
from sqlalchemy.orm import Session

from app.auth.repository import UserRepository
from app.database import get_db
from app.users.service import UserService


def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


def get_user_service(
    user_repository: UserRepository = Depends(get_user_repository)
) -> UserService:
    return UserService(user_repository)