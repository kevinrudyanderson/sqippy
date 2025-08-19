from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.organizations.models import Organization, PlanType
from app.subscriptions.models import Subscription, SubscriptionStatus
from app.subscriptions.repository import SubscriptionRepository, UsageTrackingRepository
from app.subscriptions.schemas import PlanLimits, UsageStats


class SubscriptionService:
    def __init__(self, db: Session):
        self.db = db
        self.subscription_repo = SubscriptionRepository(db)
        self.usage_repo = UsageTrackingRepository(db)

    def get_plan_limits(self, plan_type: PlanType) -> dict:
        limits = {
            PlanType.FREE: {
                "queue_limit": settings.FREE_QUEUE_LIMIT,
                "sms_credits": settings.FREE_SMS_CREDITS,
                "deactivation_days": settings.FREE_DEACTIVATION_DAYS,
            },
            PlanType.PRO: {
                "queue_limit": settings.PRO_QUEUE_LIMIT,
                "sms_credits": settings.PRO_SMS_CREDITS,
                "deactivation_days": settings.PRO_DEACTIVATION_DAYS,
            },
            PlanType.BUSINESS: {
                "queue_limit": settings.BUSINESS_QUEUE_LIMIT,
                "sms_credits": settings.BUSINESS_SMS_CREDITS,
                "deactivation_days": None,  # Never deactivates
            }
        }
        return limits.get(plan_type, limits[PlanType.FREE])

    def create_subscription(self, organization_id: str, plan_type: PlanType = PlanType.FREE) -> Subscription:
        existing = self.subscription_repo.get_by_organization(organization_id)
        if existing:
            return existing
        
        limits = self.get_plan_limits(plan_type)
        
        subscription = Subscription(
            organization_id=organization_id,
            plan_type=plan_type,
            status=SubscriptionStatus.ACTIVE,
            queue_limit=limits["queue_limit"],
            sms_credits_total=limits["sms_credits"],
            sms_credits_used=0,
            email_sent_count=0
        )
        
        if plan_type != PlanType.FREE:
            subscription.current_period_end = datetime.now(timezone.utc) + timedelta(days=30)
        
        self.db.add(subscription)
        self.db.commit()
        self.db.refresh(subscription)
        
        return subscription

    def get_organization_subscription(self, organization_id: str) -> Optional[Subscription]:
        subscription = self.subscription_repo.get_active_by_organization(organization_id)
        if not subscription:
            subscription = self.create_subscription(organization_id)
        return subscription

    def can_create_queue(self, organization_id: str) -> tuple[bool, str]:
        subscription = self.get_organization_subscription(organization_id)
        if not subscription or subscription.status != SubscriptionStatus.ACTIVE:
            return False, "No active subscription"
        
        usage = self.usage_repo.get_current_month(organization_id)
        queues_created = usage.queues_created if usage else 0
        
        if queues_created >= subscription.queue_limit:
            return False, f"Queue limit reached ({subscription.queue_limit} queues for {subscription.plan_type} plan)"
        
        return True, "Can create queue"

    def can_send_sms(self, organization_id: str, count: int = 1) -> tuple[bool, str]:
        subscription = self.get_organization_subscription(organization_id)
        if not subscription or subscription.status != SubscriptionStatus.ACTIVE:
            return False, "No active subscription"
        
        remaining = subscription.sms_credits_total - subscription.sms_credits_used
        if remaining < count:
            return False, f"Insufficient SMS credits (need {count}, have {remaining})"
        
        return True, "Can send SMS"

    def can_send_email(self, organization_id: str) -> tuple[bool, str]:
        subscription = self.get_organization_subscription(organization_id)
        if not subscription or subscription.status != SubscriptionStatus.ACTIVE:
            return False, "No active subscription"
        
        return True, "Can send email"

    def use_sms_credits(self, organization_id: str, count: int = 1) -> bool:
        subscription = self.get_organization_subscription(organization_id)
        if not subscription:
            return False
        
        can_send, _ = self.can_send_sms(organization_id, count)
        if not can_send:
            return False
        
        self.subscription_repo.update_credits_used(subscription.subscription_id, sms_used=count)
        self.usage_repo.increment_usage(organization_id, sms=count)
        self.update_organization_activity(organization_id)
        
        return True

    def track_email_sent(self, organization_id: str, count: int = 1) -> bool:
        subscription = self.get_organization_subscription(organization_id)
        if not subscription:
            return False
        
        self.subscription_repo.update_credits_used(subscription.subscription_id, emails_sent=count)
        self.usage_repo.increment_usage(organization_id, emails=count)
        self.update_organization_activity(organization_id)
        
        return True

    def track_queue_created(self, organization_id: str) -> bool:
        can_create, _ = self.can_create_queue(organization_id)
        if not can_create:
            return False
        
        self.usage_repo.increment_usage(organization_id, queues=1)
        self.update_organization_activity(organization_id)
        
        return True

    def update_organization_activity(self, organization_id: str):
        org = self.db.query(Organization).filter(
            Organization.organization_id == organization_id
        ).first()
        if org:
            org.last_activity_at = datetime.now(timezone.utc)
            self.db.commit()

    def get_plan_limits_for_organization(self, organization_id: str) -> PlanLimits:
        subscription = self.get_organization_subscription(organization_id)
        if not subscription:
            limits = self.get_plan_limits(PlanType.FREE)
            return PlanLimits(
                plan_type=PlanType.FREE,
                queue_limit=limits["queue_limit"],
                sms_credits=limits["sms_credits"],
                can_create_queue=False,
                can_send_sms=False,
                can_send_email=True,
                queues_remaining=0,
                sms_remaining=0
            )
        
        usage = self.usage_repo.get_current_month(organization_id)
        queues_created = usage.queues_created if usage else 0
        
        can_create_queue, _ = self.can_create_queue(organization_id)
        can_send_sms, _ = self.can_send_sms(organization_id)
        can_send_email, _ = self.can_send_email(organization_id)
        
        return PlanLimits(
            plan_type=subscription.plan_type,
            queue_limit=subscription.queue_limit,
            sms_credits=subscription.sms_credits_total,
            can_create_queue=can_create_queue,
            can_send_sms=can_send_sms,
            can_send_email=can_send_email,
            queues_remaining=max(0, subscription.queue_limit - queues_created),
            sms_remaining=max(0, subscription.sms_credits_total - subscription.sms_credits_used)
        )

    def get_usage_stats(self, organization_id: str) -> UsageStats:
        subscription = self.get_organization_subscription(organization_id)
        usage = self.usage_repo.get_current_month(organization_id)
        
        if not usage:
            usage = self.usage_repo.get_or_create_current_month(organization_id)
        
        return UsageStats(
            current_month=usage.month_year,
            queues_created=usage.queues_created,
            queues_limit=subscription.queue_limit if subscription else 0,
            sms_sent=usage.sms_sent,
            sms_limit=subscription.sms_credits_total if subscription else 0,
            emails_sent=usage.emails_sent,
            last_activity=usage.last_activity_at
        )

    def upgrade_plan(self, organization_id: str, new_plan: PlanType, bypass_payment: bool = False) -> Subscription:
        subscription = self.get_organization_subscription(organization_id)
        
        if not subscription:
            return self.create_subscription(organization_id, new_plan)
        
        # Prevent upgrades from FREE without payment verification
        if not bypass_payment and subscription.plan_type == PlanType.FREE and new_plan != PlanType.FREE:
            # TODO: Integrate with Stripe payment verification here
            # For now, block the upgrade
            raise ValueError("Payment verification required for plan upgrades. Please contact support.")
        
        limits = self.get_plan_limits(new_plan)
        
        subscription.plan_type = new_plan
        subscription.queue_limit = limits["queue_limit"]
        subscription.sms_credits_total = limits["sms_credits"]
        
        if new_plan != PlanType.FREE:
            subscription.current_period_end = datetime.now(timezone.utc) + timedelta(days=30)
        else:
            subscription.current_period_end = None
        
        org = self.db.query(Organization).filter(
            Organization.organization_id == organization_id
        ).first()
        if org:
            org.plan_type = new_plan
            org.plan_started_at = datetime.now(timezone.utc)
        
        self.db.commit()
        self.db.refresh(subscription)
        
        return subscription

    def cancel_subscription(self, organization_id: str) -> bool:
        subscription = self.get_organization_subscription(organization_id)
        if not subscription:
            return False
        
        subscription.status = SubscriptionStatus.CANCELLED
        subscription.plan_type = PlanType.FREE
        
        limits = self.get_plan_limits(PlanType.FREE)
        subscription.queue_limit = limits["queue_limit"]
        subscription.sms_credits_total = limits["sms_credits"]
        subscription.current_period_end = None
        
        org = self.db.query(Organization).filter(
            Organization.organization_id == organization_id
        ).first()
        if org:
            org.plan_type = PlanType.FREE
            org.plan_expires_at = datetime.now(timezone.utc)
        
        self.db.commit()
        
        return True

    def check_feature_access(self, organization_id: str, feature: str) -> bool:
        subscription = self.get_organization_subscription(organization_id)
        if not subscription or subscription.status != SubscriptionStatus.ACTIVE:
            return False
        
        feature_access = {
            "api_access": [PlanType.BUSINESS],
            "white_label": [PlanType.BUSINESS],
            "custom_branding": [PlanType.PRO, PlanType.BUSINESS],
            "advanced_analytics": [PlanType.PRO, PlanType.BUSINESS],
            "priority_support": [PlanType.BUSINESS],
        }
        
        if feature not in feature_access:
            return True
        
        return subscription.plan_type in feature_access[feature]