from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import UUID, Boolean, Column, DateTime, Enum, String, ForeignKey
from sqlalchemy.orm import relationship

from app.auth.roles import UserRole
from app.database import Base


class User(Base):
    __tablename__ = "users"

    # TODO: Remove this once we use postgres
    # user_id = Column(UUID, primary_key=True, default=uuid4)
    user_id = Column(String, primary_key=True, default=lambda: str(uuid4()))

    # Organization relationship
    organization_id = Column(String, ForeignKey("organizations.organization_id"), nullable=True)

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

    # Relationships
    organization = relationship("Organization", back_populates="users")
    # queue_entries = relationship("QueueEntry", back_populates="user")

    @property
    def is_staff_or_admin(self) -> bool:
        return self.role in [UserRole.STAFF, UserRole.ADMIN]

    @property
    def needs_password(self) -> bool:
        return self.role in [UserRole.STAFF, UserRole.ADMIN]


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    # TODO: Remove this once we use postgres
    token_id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    token = Column(String, unique=True, nullable=False, index=True)
    
    expires_at = Column(DateTime, nullable=False)
    is_revoked = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    revoked_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", backref="refresh_tokens")
