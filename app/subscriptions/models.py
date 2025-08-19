from datetime import datetime, timezone
from enum import Enum as PyEnum
from uuid import uuid4

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class PlanType(str, PyEnum):
    FREE = "FREE"
    PRO = "PRO"
    BUSINESS = "BUSINESS"


class SubscriptionStatus(str, PyEnum):
    ACTIVE = "ACTIVE"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"
    PAST_DUE = "PAST_DUE"


class Subscription(Base):
    __tablename__ = "subscriptions"

    subscription_id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    organization_id = Column(String, ForeignKey("organizations.organization_id"), nullable=False)
    
    plan_type = Column(Enum(PlanType), nullable=False, default=PlanType.FREE)
    status = Column(Enum(SubscriptionStatus), nullable=False, default=SubscriptionStatus.ACTIVE)
    
    current_period_start = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    current_period_end = Column(DateTime, nullable=True)
    
    queue_limit = Column(Integer, nullable=False, default=1)
    sms_credits_total = Column(Integer, nullable=False, default=0)
    sms_credits_used = Column(Integer, nullable=False, default=0)
    email_sent_count = Column(Integer, nullable=False, default=0)
    
    stripe_subscription_id = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    
    organization = relationship("Organization", back_populates="subscription")

    def __repr__(self):
        return f"<Subscription(id={self.subscription_id}, org={self.organization_id}, plan={self.plan_type})>"


class UsageTracking(Base):
    __tablename__ = "usage_tracking"

    tracking_id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    organization_id = Column(String, ForeignKey("organizations.organization_id"), nullable=False)
    
    month_year = Column(String, nullable=False)  # Format: "2024-01"
    queues_created = Column(Integer, nullable=False, default=0)
    sms_sent = Column(Integer, nullable=False, default=0)
    emails_sent = Column(Integer, nullable=False, default=0)
    last_activity_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    
    organization = relationship("Organization", back_populates="usage_tracking")

    def __repr__(self):
        return f"<UsageTracking(id={self.tracking_id}, org={self.organization_id}, month={self.month_year})>"