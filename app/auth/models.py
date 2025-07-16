from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import UUID, Boolean, Column, DateTime, Enum, String
from sqlalchemy.orm import relationship

from app.auth.roles import UserRole
from app.database import Base


class User(Base):
    __tablename__ = "users"

    # TODO: Remove this once we use postgres
    # user_id = Column(UUID, primary_key=True, default=uuid4)
    user_id = Column(String, primary_key=True, default=lambda: str(uuid4()))

    name = Column(String, nullable=False)

    email = Column(String, unique=True, nullable=False, index=True)
    phone_number = Column(String, unique=True, nullable=True, index=True)

    password = Column(String, nullable=False)

    role = Column(Enum(UserRole), default=UserRole.CUSTOMER, nullable=False)

    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)

    last_login = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=True
    )

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # queue_entries = relationship("QueueEntry", back_populates="user")

    @property
    def is_staff_or_admin(self) -> bool:
        return self.role in [UserRole.STAFF, UserRole.ADMIN]

    @property
    def needs_password(self) -> bool:
        return self.role in [UserRole.STAFF, UserRole.ADMIN]
