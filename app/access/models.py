import enum
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.database import Base


class AccessLevel(enum.Enum):
    """Access levels for user-location relationships"""

    VIEWER = "viewer"  # Read-only access
    MANAGER = "manager"  # Can manage services/queues, but not location settings
    OWNER = "owner"  # Full control including location settings and access management

    def __ge__(self, other):
        """Enable comparison for access level hierarchy"""
        if not isinstance(other, AccessLevel):
            return NotImplemented

        hierarchy = {
            AccessLevel.VIEWER: 1,
            AccessLevel.MANAGER: 2,
            AccessLevel.OWNER: 3,
        }
        return hierarchy[self] >= hierarchy[other]

    def __gt__(self, other):
        """Enable comparison for access level hierarchy"""
        if not isinstance(other, AccessLevel):
            return NotImplemented

        hierarchy = {
            AccessLevel.VIEWER: 1,
            AccessLevel.MANAGER: 2,
            AccessLevel.OWNER: 3,
        }
        return hierarchy[self] > hierarchy[other]


class UserLocationAccess(Base):
    """Linking table for user access to locations and their resources"""

    __tablename__ = "user_location_access"

    access_id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    location_id = Column(String, ForeignKey("locations.location_id"), nullable=False)
    access_level = Column(Enum(AccessLevel), nullable=False)

    # Audit fields
    granted_by = Column(
        String, ForeignKey("users.user_id"), nullable=True
    )  # Who granted this access
    granted_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(
        DateTime, nullable=True
    )  # Optional expiration for temporary access

    # Control fields
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships (removed back_populates since we're not using this system anymore)
    user = relationship("User", foreign_keys=[user_id])
    location = relationship("Location")
    granted_by_user = relationship("User", foreign_keys=[granted_by])

    # Constraints
    __table_args__ = (
        UniqueConstraint("user_id", "location_id", name="unique_user_location_access"),
    )

    def __repr__(self):
        return f"<UserLocationAccess(user_id={self.user_id}, location_id={self.location_id}, access_level={self.access_level})>"

    @property
    def is_valid(self) -> bool:
        """Check if this access record is currently valid"""
        if not self.is_active:
            return False

        if self.expires_at and datetime.now(timezone.utc) > self.expires_at:
            return False

        return True

    def can_manage_services(self) -> bool:
        """Check if this access level allows managing services"""
        return self.access_level >= AccessLevel.MANAGER and self.is_valid

    def can_manage_location(self) -> bool:
        """Check if this access level allows managing location settings"""
        return self.access_level >= AccessLevel.OWNER and self.is_valid

    def can_grant_access(self) -> bool:
        """Check if this access level allows granting access to others"""
        return self.access_level >= AccessLevel.OWNER and self.is_valid
