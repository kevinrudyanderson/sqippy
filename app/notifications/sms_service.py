from typing import Optional, Tuple

from sqlalchemy.orm import Session

from app.notifications.service import notification_service
from app.subscriptions.service import SubscriptionService


class SMSService:
    """Service for managing SMS notifications with quota tracking"""

    def __init__(self, db: Session):
        self.db = db
        self.subscription_service = SubscriptionService(db)

    async def send_queue_notification_sms(
        self,
        organization_id: str,
        customer_phone: str,
        customer_name: str,
        queue_name: str,
        location_name: str,
        notification_type: str,
        **kwargs,
    ) -> Tuple[bool, str]:
        """
        Send SMS notification with quota tracking

        Args:
            organization_id: Organization ID for quota tracking
            customer_phone: Customer's phone number
            customer_name: Customer's name
            queue_name: Name of the queue
            notification_type: Type of notification ('next_in_line', 'almost_your_turn', 'queue_subscription')
            **kwargs: Additional parameters specific to notification type

        Returns:
            Tuple of (success: bool, message: str)
        """

        # Check if organization can send SMS
        can_send, quota_message = self.subscription_service.can_send_sms(
            organization_id
        )
        if not can_send:
            return False, f"SMS quota exceeded: {quota_message}"

        # Send the appropriate SMS based on notification type
        try:
            if notification_type == "next_in_line":
                service_location = kwargs.get(
                    "service_location", "the service location"
                )
                result = await notification_service.send_next_in_line_sms(
                    customer_phone, customer_name, queue_name, service_location
                )
            elif notification_type == "almost_your_turn":
                position = kwargs.get("position", 1)
                estimated_wait = kwargs.get("estimated_wait", "a few minutes")
                result = await notification_service.send_almost_your_turn_sms(
                    customer_phone, customer_name, queue_name, position, estimated_wait
                )
            elif notification_type == "queue_subscription":
                position = kwargs.get("position", 1)
                estimated_wait = kwargs.get("estimated_wait", "a few minutes")
                result = await notification_service.send_queue_subscription_sms(
                    customer_phone,
                    customer_name,
                    queue_name,
                    location_name,
                    position,
                    estimated_wait,
                )
            else:
                return False, f"Unknown notification type: {notification_type}"

            if result.success:
                # Deduct SMS credit from quota
                credit_used = self.subscription_service.use_sms_credits(
                    organization_id, 1
                )
                if credit_used:
                    return True, "SMS sent successfully"
                else:
                    return False, "SMS sent but failed to update quota"
            else:
                return False, f"SMS sending failed: {result.error}"

        except Exception as e:
            return False, f"SMS service error: {str(e)}"

    async def send_custom_sms(
        self, organization_id: str, customer_phone: str, message: str
    ) -> Tuple[bool, str]:
        """Send custom SMS message with quota tracking"""

        # Check if organization can send SMS
        can_send, quota_message = self.subscription_service.can_send_sms(
            organization_id
        )
        if not can_send:
            return False, f"SMS quota exceeded: {quota_message}"

        try:
            result = await notification_service.send_custom_sms(customer_phone, message)

            if result.success:
                # Deduct SMS credit from quota
                credit_used = self.subscription_service.use_sms_credits(
                    organization_id, 1
                )
                if credit_used:
                    return True, "SMS sent successfully"
                else:
                    return False, "SMS sent but failed to update quota"
            else:
                return False, f"SMS sending failed: {result.error}"

        except Exception as e:
            return False, f"SMS service error: {str(e)}"

    def get_sms_quota_status(self, organization_id: str) -> dict:
        """Get current SMS quota status for an organization"""
        subscription = self.subscription_service.get_organization_subscription(
            organization_id
        )

        if not subscription:
            return {
                "has_subscription": False,
                "total_credits": 0,
                "used_credits": 0,
                "remaining_credits": 0,
                "can_send_sms": False,
            }

        remaining = subscription.sms_credits_total - subscription.sms_credits_used
        can_send, _ = self.subscription_service.can_send_sms(organization_id)

        return {
            "has_subscription": True,
            "plan_type": subscription.plan_type.value,
            "total_credits": subscription.sms_credits_total,
            "used_credits": subscription.sms_credits_used,
            "remaining_credits": remaining,
            "can_send_sms": can_send,
        }
