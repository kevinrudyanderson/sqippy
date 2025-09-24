import os
from typing import Any, Dict, Optional

from .providers.base import BaseNotificationProvider, NotificationResult
from .providers.postmark import PostmarkEmailProvider
from .providers.prelude import PreludeSMSProvider
from .providers.twilio import TwilioSMSProvider
from .templates import EmailTemplates, SMSTemplates


class NotificationService:
    def __init__(self):
        self.email_provider = self._initialize_email_provider()
        self.sms_provider = self._initialize_sms_provider()
        self.email_templates = EmailTemplates()
        self.sms_templates = SMSTemplates()

    def _initialize_email_provider(self) -> Optional[BaseNotificationProvider]:
        postmark_token = os.getenv("POSTMARK_API_TOKEN")
        from_email = os.getenv("POSTMARK_FROM_EMAIL")

        if postmark_token and from_email:
            return PostmarkEmailProvider(
                {"api_token": postmark_token, "from_email": from_email}
            )
        return None

    def _initialize_sms_provider(self) -> Optional[BaseNotificationProvider]:
        # Check for Twilio configuration first (preferred)
        twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        twilio_phone_number = os.getenv("TWILIO_PHONE_NUMBER")

        if all([twilio_account_sid, twilio_auth_token]):
            return TwilioSMSProvider(
                {
                    "account_sid": twilio_account_sid,
                    "auth_token": twilio_auth_token,
                    "phone_number": twilio_phone_number,  # Can be None
                }
            )

        # Fallback to Prelude if Twilio not configured
        prelude_token = os.getenv("PRELUDE_API_TOKEN")
        if prelude_token:
            return PreludeSMSProvider({"api_token": prelude_token})

        return None

    async def send_queue_subscription_email(
        self,
        customer_email: str,
        customer_name: str,
        queue_name: str,
        position: int,
        estimated_wait: str,
    ) -> NotificationResult:
        if not self.email_provider:
            return NotificationResult(
                success=False, error="Email provider not configured"
            )

        template = self.email_templates.queue_subscription(
            customer_name=customer_name,
            queue_name=queue_name,
            position=position,
            estimated_wait=estimated_wait,
        )

        return await self.email_provider.send(
            to=customer_email,
            subject=template["subject"],
            body=template["text_body"],
            html_body=template["html_body"],
            tag="queue-subscription",
        )

    async def send_queue_subscription_sms(
        self,
        customer_phone: str,
        customer_name: str,
        queue_name: str,
        location_name: str,
        position: int,
        estimated_wait: str,
    ) -> NotificationResult:
        if not self.sms_provider:
            return NotificationResult(
                success=False, error="SMS provider not configured"
            )

        message = self.sms_templates.queue_subscription(
            customer_name=customer_name,
            queue_name=queue_name,
            location_name=location_name,
            position=position,
            estimated_wait=estimated_wait,
        )

        return await self.sms_provider.send(
            to=customer_phone,
            subject="",
            body=message,
            message=message,
        )

    async def send_next_in_line_email(
        self,
        customer_email: str,
        customer_name: str,
        queue_name: str,
        service_location: str,
    ) -> NotificationResult:
        if not self.email_provider:
            return NotificationResult(
                success=False, error="Email provider not configured"
            )

        template = self.email_templates.next_in_line(
            customer_name=customer_name,
            queue_name=queue_name,
            service_location=service_location,
        )

        return await self.email_provider.send(
            to=customer_email,
            subject=template["subject"],
            body=template["text_body"],
            html_body=template["html_body"],
            tag="next-in-line",
        )

    async def send_next_in_line_sms(
        self,
        customer_phone: str,
        customer_name: str,
        queue_name: str,
        service_location: str,
    ) -> NotificationResult:
        if not self.sms_provider:
            return NotificationResult(
                success=False, error="SMS provider not configured"
            )

        message = self.sms_templates.next_in_line(
            customer_name=customer_name,
            queue_name=queue_name,
            service_location=service_location,
        )

        return await self.sms_provider.send(
            to=customer_phone,
            subject="",
            body=message,
            message=message,
        )

    async def send_almost_your_turn_email(
        self,
        customer_email: str,
        customer_name: str,
        queue_name: str,
        position: int,
        estimated_wait: str,
    ) -> NotificationResult:
        if not self.email_provider:
            return NotificationResult(
                success=False, error="Email provider not configured"
            )

        template = self.email_templates.almost_your_turn(
            customer_name=customer_name,
            queue_name=queue_name,
            position=position,
            estimated_wait=estimated_wait,
        )

        return await self.email_provider.send(
            to=customer_email,
            subject=template["subject"],
            body=template["text_body"],
            html_body=template["html_body"],
            tag="almost-your-turn",
        )

    async def send_almost_your_turn_sms(
        self,
        customer_phone: str,
        customer_name: str,
        queue_name: str,
        position: int,
        estimated_wait: str,
    ) -> NotificationResult:
        if not self.sms_provider:
            return NotificationResult(
                success=False, error="SMS provider not configured"
            )

        message = self.sms_templates.almost_your_turn(
            customer_name=customer_name,
            queue_name=queue_name,
            position=position,
            estimated_wait=estimated_wait,
        )

        return await self.sms_provider.send(
            to=customer_phone,
            subject="",
            body=message,
            message=message,
        )

    async def send_custom_email(
        self,
        to: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        **kwargs
    ) -> NotificationResult:
        if not self.email_provider:
            return NotificationResult(
                success=False, error="Email provider not configured"
            )

        return await self.email_provider.send(
            to=to, subject=subject, body=body, html_body=html_body, **kwargs
        )

    async def send_custom_sms(
        self, to: str, message: str, **kwargs
    ) -> NotificationResult:
        if not self.sms_provider:
            return NotificationResult(
                success=False, error="SMS provider not configured"
            )

        return await self.sms_provider.send(
            to=to, subject="", body=message, message=message, **kwargs
        )


notification_service = NotificationService()
