import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.organizations.models import Organization, PlanType
from app.queue.models import Queue, QueueStatus
from app.subscriptions.models import UsageTracking

logger = logging.getLogger(__name__)

# Create a separate engine for the scheduler to avoid conflicts
scheduler_engine = create_engine(settings.SQLALCHEMY_DATABASE_URL)
SchedulerSession = sessionmaker(bind=scheduler_engine, expire_on_commit=False)


class SubscriptionScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.setup_jobs()

    def setup_jobs(self):
        # Run queue deactivation check daily at midnight
        self.scheduler.add_job(
            self.check_and_deactivate_queues,
            trigger="cron",
            hour=0,
            minute=0,
            id="queue_deactivation",
            replace_existing=True
        )
        
        # Send warning emails daily at 10 AM
        self.scheduler.add_job(
            self.send_deactivation_warnings,
            trigger="cron",
            hour=10,
            minute=0,
            id="deactivation_warnings",
            replace_existing=True
        )
        
        # Reset monthly usage on the 1st of each month
        self.scheduler.add_job(
            self.reset_monthly_usage,
            trigger="cron",
            day=1,
            hour=0,
            minute=0,
            id="monthly_reset",
            replace_existing=True
        )

    async def check_and_deactivate_queues(self):
        """Check and deactivate queues for inactive organizations"""
        logger.info("Starting queue deactivation check")
        
        with SchedulerSession() as db:
            try:
                now = datetime.now(timezone.utc)
                
                # Get all organizations with their deactivation rules
                organizations = db.query(Organization).filter(
                    Organization.is_active == True
                ).all()
                
                for org in organizations:
                    deactivation_days = self.get_deactivation_days(org.plan_type)
                    
                    if deactivation_days is None:
                        # Business plan - never deactivates
                        continue
                    
                    # Check if organization has been inactive
                    if org.last_activity_at:
                        days_inactive = (now - org.last_activity_at).days
                        
                        if days_inactive >= deactivation_days:
                            # Deactivate all queues for this organization
                            queues = db.query(Queue).filter(
                                Queue.organization_id == org.organization_id,
                                Queue.status == QueueStatus.ACTIVE
                            ).all()
                            
                            for queue in queues:
                                queue.status = QueueStatus.INACTIVE
                                logger.info(f"Deactivated queue {queue.queue_id} for organization {org.organization_id}")
                            
                            db.commit()
                            logger.info(f"Deactivated {len(queues)} queues for organization {org.organization_id}")
                
            except Exception as e:
                logger.error(f"Error in queue deactivation: {e}")
                db.rollback()

    async def send_deactivation_warnings(self):
        """Send warning emails for upcoming deactivations"""
        logger.info("Checking for deactivation warnings")
        
        with SchedulerSession() as db:
            try:
                now = datetime.now(timezone.utc)
                
                organizations = db.query(Organization).filter(
                    Organization.is_active == True
                ).all()
                
                for org in organizations:
                    deactivation_days = self.get_deactivation_days(org.plan_type)
                    
                    if deactivation_days is None or not org.last_activity_at:
                        continue
                    
                    days_inactive = (now - org.last_activity_at).days
                    days_until_deactivation = deactivation_days - days_inactive
                    
                    # Send warnings at 7 days and 1 day before deactivation
                    if days_until_deactivation in [7, 1]:
                        # TODO: Integrate with email service when ready
                        logger.info(
                            f"Warning: Organization {org.organization_id} will be deactivated "
                            f"in {days_until_deactivation} day(s)"
                        )
                
            except Exception as e:
                logger.error(f"Error sending deactivation warnings: {e}")

    async def reset_monthly_usage(self):
        """Reset SMS credits and usage tracking at the start of each month"""
        logger.info("Resetting monthly usage")
        
        with SchedulerSession() as db:
            try:
                from app.subscriptions.models import Subscription
                
                # Reset SMS credits for all active subscriptions
                subscriptions = db.query(Subscription).filter(
                    Subscription.status == "ACTIVE"
                ).all()
                
                for sub in subscriptions:
                    # Reset SMS credits used
                    sub.sms_credits_used = 0
                    sub.email_sent_count = 0
                    logger.info(f"Reset usage for subscription {sub.subscription_id}")
                
                db.commit()
                logger.info(f"Reset usage for {len(subscriptions)} subscriptions")
                
            except Exception as e:
                logger.error(f"Error resetting monthly usage: {e}")
                db.rollback()

    def get_deactivation_days(self, plan_type: PlanType) -> Optional[int]:
        """Get deactivation days for a plan type"""
        if plan_type == PlanType.FREE:
            return settings.FREE_DEACTIVATION_DAYS
        elif plan_type == PlanType.PRO:
            return settings.PRO_DEACTIVATION_DAYS
        elif plan_type == PlanType.BUSINESS:
            return None  # Never deactivates
        return settings.FREE_DEACTIVATION_DAYS

    def start(self):
        """Start the scheduler"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Subscription scheduler started")

    def stop(self):
        """Stop the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Subscription scheduler stopped")


# Global scheduler instance
subscription_scheduler = SubscriptionScheduler()


async def start_scheduler():
    """Start the subscription scheduler"""
    subscription_scheduler.start()


async def stop_scheduler():
    """Stop the subscription scheduler"""
    subscription_scheduler.stop()