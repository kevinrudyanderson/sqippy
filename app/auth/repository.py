from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.auth.models import User
from app.auth.roles import UserRole
from app.auth.schemas import CustomerSignUp, StaffCreate, UserUpdate
from app.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, db: Session):
        super().__init__(db, User)

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def get_or_create_customer(self, customer_signup: CustomerSignUp) -> User:
        user = self.get_by_email(customer_signup.email)
        if not user:
            user = User(
                **customer_signup.model_dump(),
                role=UserRole.CUSTOMER,
            )
            user = self.create(user)
        return user

    def update_user(self, user_id: UUID, user_update: UserUpdate) -> User:
        user = self.get(user_id)
        if not user:
            raise ValueError("User not found")
        return self.update_from_schema(user, user_update)

    def create_staff_user(self, staff_create: StaffCreate) -> User:
        user = User(
            **staff_create.model_dump(),
        )
        return self.create(user)
