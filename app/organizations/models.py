from datetime import datetime, timezone
from enum import Enum as PyEnum
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, Enum, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class PlanType(str, PyEnum):
    FREE = "FREE"
    PRO = "PRO"
    BUSINESS = "BUSINESS"


class Organization(Base):
    __tablename__ = "organizations"

    organization_id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    
    # Basic info
    name = Column(String, nullable=False)
    business_type = Column(String, nullable=True)  # e.g., "restaurant", "medical", "retail"
    description = Column(Text, nullable=True)
    
    # Contact info
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    website = Column(String, nullable=True)
    
    # Address
    address = Column(String, nullable=True)
    city = Column(String, nullable=True)
    country = Column(String, nullable=True, default="NL")
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Subscription fields
    plan_type = Column(Enum(PlanType), nullable=False, default=PlanType.FREE)
    plan_started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    plan_expires_at = Column(DateTime, nullable=True)
    stripe_customer_id = Column(String, nullable=True)
    stripe_subscription_id = Column(String, nullable=True)
    last_activity_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    users = relationship("User", back_populates="organization")
    locations = relationship("Location", back_populates="organization", cascade="all, delete-orphan")
    subscription = relationship("Subscription", back_populates="organization", uselist=False)
    usage_tracking = relationship("UsageTracking", back_populates="organization")

    def __repr__(self):
        return f"<Organization(id={self.organization_id}, name={self.name})>"