import json
from typing import Any, Dict, List, Optional

import aiohttp

from .base import BaseNotificationProvider, NotificationResult, NotificationStatus


class PostmarkEmailProvider(BaseNotificationProvider):
    BASE_URL = "https://api.postmarkapp.com"

    def initialize(self) -> None:
        self.api_token = self.config.get("api_token")
        if not self.api_token:
            raise ValueError("Postmark API token is required")

        self.from_email = self.config.get("from_email")
        if not self.from_email:
            raise ValueError("From email address is required")

        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Postmark-Server-Token": self.api_token,
        }

    async def send(
        self,
        to: str | List[str],
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        **kwargs,
    ) -> NotificationResult:
        if isinstance(to, list):
            to = ",".join(to)

        payload = {
            "From": self.from_email,
            "To": to,
            "Subject": subject,
            "TextBody": body,
        }

        if html_body:
            payload["HtmlBody"] = html_body

        if "reply_to" in kwargs:
            payload["ReplyTo"] = kwargs["reply_to"]

        if "cc" in kwargs:
            cc = kwargs["cc"]
            if isinstance(cc, list):
                cc = ",".join(cc)
            payload["Cc"] = cc

        if "bcc" in kwargs:
            bcc = kwargs["bcc"]
            if isinstance(bcc, list):
                bcc = ",".join(bcc)
            payload["Bcc"] = bcc

        if "tag" in kwargs:
            payload["Tag"] = kwargs["tag"]

        if "metadata" in kwargs:
            payload["Metadata"] = kwargs["metadata"]

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.BASE_URL}/email",
                    headers=self.headers,
                    data=json.dumps(payload),
                ) as response:
                    result = await response.json()

                    if response.status == 200:
                        return NotificationResult(
                            success=True,
                            message_id=result.get("MessageID"),
                            status=NotificationStatus.SENT,
                            metadata={"postmark_response": result},
                        )
                    else:
                        return NotificationResult(
                            success=False,
                            status=NotificationStatus.FAILED,
                            error=result.get("Message", "Unknown error"),
                            metadata={"postmark_response": result},
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
        if isinstance(to, list):
            to = ",".join(to)

        payload = {
            "From": self.from_email,
            "To": to,
            "TemplateId": template_id,
            "TemplateModel": template_data,
        }

        if "reply_to" in kwargs:
            payload["ReplyTo"] = kwargs["reply_to"]

        if "cc" in kwargs:
            cc = kwargs["cc"]
            if isinstance(cc, list):
                cc = ",".join(cc)
            payload["Cc"] = cc

        if "bcc" in kwargs:
            bcc = kwargs["bcc"]
            if isinstance(bcc, list):
                bcc = ",".join(bcc)
            payload["Bcc"] = bcc

        if "tag" in kwargs:
            payload["Tag"] = kwargs["tag"]

        if "metadata" in kwargs:
            payload["Metadata"] = kwargs["metadata"]

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.BASE_URL}/email/withTemplate",
                    headers=self.headers,
                    data=json.dumps(payload),
                ) as response:
                    result = await response.json()

                    if response.status == 200:
                        return NotificationResult(
                            success=True,
                            message_id=result.get("MessageID"),
                            status=NotificationStatus.SENT,
                            metadata={"postmark_response": result},
                        )
                    else:
                        return NotificationResult(
                            success=False,
                            status=NotificationStatus.FAILED,
                            error=result.get("Message", "Unknown error"),
                            metadata={"postmark_response": result},
                        )
        except Exception as e:
            return NotificationResult(
                success=False, status=NotificationStatus.FAILED, error=str(e)
            )

    async def get_status(self, message_id: str) -> NotificationStatus:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.BASE_URL}/messages/outbound/{message_id}/details",
                    headers=self.headers,
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        status = result.get("Status", "").lower()

                        if status == "sent":
                            return NotificationStatus.SENT
                        elif status == "delivered":
                            return NotificationStatus.DELIVERED
                        elif status == "bounced":
                            return NotificationStatus.BOUNCED
                        else:
                            return NotificationStatus.PENDING
                    else:
                        return NotificationStatus.FAILED
        except Exception:
            return NotificationStatus.FAILED
