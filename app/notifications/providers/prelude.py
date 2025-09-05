import json
from typing import Any, Dict, List, Optional

import aiohttp

from .base import BaseNotificationProvider, NotificationResult, NotificationStatus


class PreludeSMSProvider(BaseNotificationProvider):
    BASE_URL = "https://api.prelude.dev/v2"

    def initialize(self) -> None:
        self.api_token = self.config.get("api_token")
        if not self.api_token:
            raise ValueError("Prelude API token is required")

        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_token}",
        }

    async def send(
        self,
        to: str | List[str],
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        **kwargs,
    ) -> NotificationResult:
        """Send SMS using Prelude Transactional API"""
        # For SMS, we only use the first recipient if multiple are provided
        phone_number = to[0] if isinstance(to, list) else to

        # Clean phone number (remove any formatting)
        phone_number = self._clean_phone_number(phone_number)

        # Check if we should use template-based sending
        template_id = kwargs.get("template_id")
        if template_id:
            # Use template-based sending
            payload = {
                "to": phone_number,
                "template_id": template_id,
                "template_data": kwargs.get("template_data", {}),
            }
        else:
            # Use direct message sending
            payload = {"to": phone_number, "message": kwargs.get("message", body)}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.BASE_URL}/transactional",
                    headers=self.headers,
                    data=json.dumps(payload),
                ) as response:
                    result = await response.json()
                    print(result)

                    if response.status == 200:
                        return NotificationResult(
                            success=True,
                            message_id=result.get("id") or result.get("message_id"),
                            status=NotificationStatus.SENT,
                            metadata={"prelude_response": result},
                        )
                    else:
                        # Extract full error information from Prelude response
                        error_info = result.get("error", {})
                        error_message = error_info.get("message", "Unknown error")
                        error_code = error_info.get("code", "")
                        error_type = error_info.get("type", "")
                        request_id = error_info.get("request_id", "")

                        # Construct a comprehensive error message
                        full_error = f"{error_message}"
                        if error_code:
                            full_error += f" (Code: {error_code})"
                        if error_type:
                            full_error += f" (Type: {error_type})"
                        if request_id:
                            full_error += f" (Request ID: {request_id})"

                        return NotificationResult(
                            success=False,
                            status=NotificationStatus.FAILED,
                            error=full_error,
                            metadata={
                                "prelude_response": result,
                                "error_details": {
                                    "code": error_code,
                                    "type": error_type,
                                    "request_id": request_id,
                                    "message": error_message,
                                },
                            },
                        )
        except Exception as e:
            return NotificationResult(
                success=False, status=NotificationStatus.FAILED, error=str(e)
            )

    async def send_template(
        self,
        to: str | List[str],
        template_id: str,
        template_data: Dict[str, Any],
        **kwargs,
    ) -> NotificationResult:
        """Send templated SMS using Prelude API"""
        # Use the send method with template_id parameter
        return await self.send(
            to=to,
            subject="",
            body="",
            template_id=template_id,
            template_data=template_data,
            **kwargs,
        )

    async def get_status(self, message_id: str) -> NotificationStatus:
        """Get SMS delivery status from Prelude"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.BASE_URL}/transactional/{message_id}",
                    headers=self.headers,
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        status = result.get("status", "").lower()

                        # Map Prelude statuses to our internal statuses
                        status_map = {
                            "pending": NotificationStatus.PENDING,
                            "sent": NotificationStatus.SENT,
                            "delivered": NotificationStatus.DELIVERED,
                            "failed": NotificationStatus.FAILED,
                        }
                        return status_map.get(status, NotificationStatus.PENDING)
                    else:
                        return NotificationStatus.FAILED
        except Exception:
            return NotificationStatus.FAILED

    def _clean_phone_number(self, phone: str) -> str:
        """Clean phone number for international format"""
        # Remove any non-digit characters except +
        cleaned = "".join(c for c in phone if c.isdigit() or c == "+")

        # Ensure it starts with + for international format
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
