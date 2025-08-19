from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from app.base.repositories import BaseRepository
from app.subscriptions.models import Subscription, UsageTracking


class SubscriptionRepository(BaseRepository[Subscription]):
    def __init__(self, db: Session):
        super().__init__(Subscription, db)

    def get_by_organization(self, organization_id: str) -> Optional[Subscription]:
        return self.db.query(Subscription).filter(
            Subscription.organization_id == organization_id
        ).first()

    def get_active_by_organization(self, organization_id: str) -> Optional[Subscription]:
        return self.db.query(Subscription).filter(
            Subscription.organization_id == organization_id,
            Subscription.status == "ACTIVE"
        ).first()

    def update_credits_used(self, subscription_id: str, sms_used: int = 0, emails_sent: int = 0) -> Optional[Subscription]:
        subscription = self.get(subscription_id)
        if subscription:
            if sms_used > 0:
                subscription.sms_credits_used += sms_used
            if emails_sent > 0:
                subscription.email_sent_count += emails_sent
            self.db.commit()
            self.db.refresh(subscription)
        return subscription


class UsageTrackingRepository(BaseRepository[UsageTracking]):
    def __init__(self, db: Session):
        super().__init__(UsageTracking, db)

    def get_current_month(self, organization_id: str) -> Optional[UsageTracking]:
        current_month = datetime.now(timezone.utc).strftime("%Y-%m")
        return self.db.query(UsageTracking).filter(
            UsageTracking.organization_id == organization_id,
            UsageTracking.month_year == current_month
        ).first()

    def get_or_create_current_month(self, organization_id: str) -> UsageTracking:
        current_month = datetime.now(timezone.utc).strftime("%Y-%m")
        usage = self.get_current_month(organization_id)
        
        if not usage:
            usage = UsageTracking(
                organization_id=organization_id,
                month_year=current_month
            )
            self.db.add(usage)
            self.db.commit()
            self.db.refresh(usage)
        
        return usage

    def increment_usage(self, organization_id: str, queues: int = 0, sms: int = 0, emails: int = 0) -> UsageTracking:
        usage = self.get_or_create_current_month(organization_id)
        
        if queues > 0:
            usage.queues_created += queues
        if sms > 0:
            usage.sms_sent += sms
        if emails > 0:
            usage.emails_sent += emails
        
        usage.last_activity_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(usage)
        
        return usage

    def get_organization_history(self, organization_id: str, limit: int = 12) -> List[UsageTracking]:
        return self.db.query(UsageTracking).filter(
            UsageTracking.organization_id == organization_id
        ).order_by(UsageTracking.month_year.desc()).limit(limit).all()