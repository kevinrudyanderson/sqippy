from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.subscriptions.models import PlanType, SubscriptionStatus


class SubscriptionBase(BaseModel):
    plan_type: PlanType
    status: SubscriptionStatus = SubscriptionStatus.ACTIVE


class SubscriptionCreate(SubscriptionBase):
    organization_id: str
    queue_limit: int
    sms_credits_total: int
    sms_credits_used: int = 0
    email_sent_count: int = 0


class SubscriptionUpdate(BaseModel):
    plan_type: Optional[PlanType] = None
    status: Optional[SubscriptionStatus] = None
    sms_credits_used: Optional[int] = None
    email_sent_count: Optional[int] = None


class SubscriptionResponse(SubscriptionBase):
    subscription_id: str
    organization_id: str
    current_period_start: datetime
    current_period_end: Optional[datetime]
    queue_limit: int
    sms_credits_total: int
    sms_credits_used: int
    sms_credits_remaining: int
    email_sent_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @property
    def sms_credits_remaining(self) -> int:
        return max(0, self.sms_credits_total - self.sms_credits_used)


class UsageTrackingBase(BaseModel):
    month_year: str
    queues_created: int = 0
    sms_sent: int = 0
    emails_sent: int = 0


class UsageTrackingCreate(UsageTrackingBase):
    organization_id: str


class UsageTrackingUpdate(BaseModel):
    queues_created: Optional[int] = None
    sms_sent: Optional[int] = None
    emails_sent: Optional[int] = None
    last_activity_at: Optional[datetime] = None


class UsageTrackingResponse(UsageTrackingBase):
    tracking_id: str
    organization_id: str
    last_activity_at: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PlanLimits(BaseModel):
    plan_type: PlanType
    queue_limit: int
    sms_credits: int
    can_create_queue: bool
    can_send_sms: bool
    can_send_email: bool
    queues_remaining: int
    sms_remaining: int


class UpgradePlanRequest(BaseModel):
    new_plan: PlanType


class UsageStats(BaseModel):
    current_month: str
    queues_created: int
    queues_limit: int
    sms_sent: int
    sms_limit: int
    emails_sent: int
    last_activity: datetime