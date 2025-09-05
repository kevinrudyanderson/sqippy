from typing import Any, Dict, List, Optional

from twilio.base.exceptions import TwilioException
from twilio.rest import Client

from .base import BaseNotificationProvider, NotificationResult, NotificationStatus


class TwilioSMSProvider(BaseNotificationProvider):
    def initialize(self) -> None:
        self.account_sid = self.config.get("account_sid")
        self.auth_token = self.config.get("auth_token")
        self.phone_number = self.config.get("phone_number")

        if not all([self.account_sid, self.auth_token]):
            raise ValueError("Twilio account_sid and auth_token are required")

        self.client = Client(self.account_sid, self.auth_token)

    async def send(
        self,
        to: str | List[str],
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        **kwargs,
    ) -> NotificationResult:
        """Send SMS using Twilio API"""
        # Check if phone number is configured
        if not self.phone_number:
            return NotificationResult(
                success=False,
                status=NotificationStatus.FAILED,
                error="Twilio phone_number is required for sending SMS",
            )

        # For SMS, we only use the first recipient if multiple are provided
        phone_number = to[0] if isinstance(to, list) else to

        # Clean phone number
        phone_number = self._clean_phone_number(phone_number)

        # Use message from kwargs if provided, otherwise use body
        message = kwargs.get("message", body)

        try:
            message_obj = self.client.messages.create(
                body=message, from_=self.phone_number, to=phone_number
            )

            return NotificationResult(
                success=True,
                message_id=message_obj.sid,
                status=NotificationStatus.SENT,
                metadata={
                    "twilio_response": {
                        "sid": message_obj.sid,
                        "status": message_obj.status,
                        "to": message_obj.to,
                        "from": message_obj.from_,
                        "body": message_obj.body,
                        "date_created": (
                            message_obj.date_created.isoformat()
                            if message_obj.date_created
                            else None
                        ),
                        "date_sent": (
                            message_obj.date_sent.isoformat()
                            if message_obj.date_sent
                            else None
                        ),
                        "price": message_obj.price,
                        "price_unit": message_obj.price_unit,
                    }
                },
            )

        except TwilioException as e:
            return NotificationResult(
                success=False,
                status=NotificationStatus.FAILED,
                error=f"Twilio error: {str(e)}",
                metadata={"twilio_error": str(e)},
            )
        except Exception as e:
            return NotificationResult(
                success=False,
                status=NotificationStatus.FAILED,
                error=f"Unexpected error: {str(e)}",
            )

    async def send_template(
        self,
        to: str | List[str],
        template_id: str,
        template_data: Dict[str, Any],
        **kwargs,
    ) -> NotificationResult:
        """Send templated SMS using Twilio API"""
        # For Twilio, we'll use the message from template_data or fall back to a simple template
        message = template_data.get("message", "")

        # If no message provided, create a basic template message
        if not message:
            message = f"Template {template_id} with data: {template_data}"

        return await self.send(to=to, subject="", body=message, **kwargs)

    async def get_status(self, message_id: str) -> NotificationStatus:
        """Get SMS delivery status from Twilio"""
        try:
            message = self.client.messages(message_id).fetch()

            # Map Twilio statuses to our internal statuses
            status_map = {
                "queued": NotificationStatus.PENDING,
                "sending": NotificationStatus.PENDING,
                "sent": NotificationStatus.SENT,
                "delivered": NotificationStatus.DELIVERED,
                "undelivered": NotificationStatus.FAILED,
                "failed": NotificationStatus.FAILED,
            }

            return status_map.get(message.status, NotificationStatus.PENDING)

        except TwilioException:
            return NotificationStatus.FAILED
        except Exception:
            return NotificationStatus.FAILED

    def _clean_phone_number(self, phone: str) -> str:
        """Clean phone number for E.164 format"""
        # Remove any non-digit characters except +
        cleaned = "".join(c for c in phone if c.isdigit() or c == "+")

        # Ensure it starts with + for E.164 format
        if not cleaned.startswith("+"):
            # Assume US number if no country code
            if len(cleaned) == 10:
                cleaned = "+1" + cleaned
            elif len(cleaned) == 11 and cleaned.startswith("1"):
                cleaned = "+" + cleaned
            else:
                # Try to add + if it looks like an international number
                cleaned = "+" + cleaned

        return cleaned
