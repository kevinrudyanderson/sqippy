from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.auth.models import User
from app.auth.roles import UserRole
from app.auth.schemas import StaffCreate, UserUpdate
from app.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, db: Session):
        super().__init__(db, User)

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()


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

    def update_profile(self, user_id: str, updates: dict) -> User:
        """Update user profile information"""
        user = self.get(user_id)
        if not user:
            raise ValueError("User not found")
        
        # Whitelist of fields that users are allowed to update
        ALLOWED_PROFILE_FIELDS = {'name', 'email', 'phone_number', 'password', 'is_active'}
        
        for field, value in updates.items():
            # Only update whitelisted fields
            if field in ALLOWED_PROFILE_FIELDS and hasattr(user, field) and value is not None:
                setattr(user, field, value)
        
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_by_phone(self, phone_number: str) -> Optional[User]:
        """Get user by phone number"""
        return self.db.query(User).filter(User.phone_number == phone_number).first()

    def email_exists(self, email: str, exclude_user_id: Optional[str] = None) -> bool:
        """Check if email exists for another user"""
        query = self.db.query(User).filter(User.email == email)
        if exclude_user_id:
            query = query.filter(User.user_id != exclude_user_id)
        return query.first() is not None

    def phone_exists(self, phone_number: str, exclude_user_id: Optional[str] = None) -> bool:
        """Check if phone number exists for another user"""
        query = self.db.query(User).filter(User.phone_number == phone_number)
        if exclude_user_id:
            query = query.filter(User.user_id != exclude_user_id)
        return query.first() is not None
