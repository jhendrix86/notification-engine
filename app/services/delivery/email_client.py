"""
Real email delivery via SendGrid's Mail Send API.

https://www.twilio.com/docs/sendgrid/api-reference/mail-send/mail-send

Same pattern as marketing-automation-engine/app/services/esp/sendgrid_client.py
(raw httpx POST, not the sendgrid SDK package) - kept as its own copy
here rather than an inter-repo import, since every engine in this fleet
is its own independent repo/deployable.
"""

import httpx
from loguru import logger

from app.config import settings
from app.services.delivery import SendResult

_API_URL = "https://api.sendgrid.com/v3/mail/send"


class EmailClient:
    def __init__(self):
        self.api_key = settings.sendgrid_api_key
        self.default_from = settings.default_email_from

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    async def send(self, to_email: str, subject: str, message: str, from_email: str = None) -> SendResult:
        if not self.configured:
            return SendResult(success=False, error="SendGrid is not configured (SENDGRID_API_KEY)")

        payload = {
            "personalizations": [{"to": [{"email": to_email}]}],
            "from": {"email": from_email or self.default_from},
            "subject": subject or "(no subject)",
            "content": [{"type": "text/html", "value": message or " "}],
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    _API_URL,
                    headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                    json=payload,
                )
        except httpx.HTTPError as exc:
            logger.error(f"SendGrid request failed: {exc}")
            return SendResult(success=False, error=f"SendGrid request failed: {exc}")

        if response.status_code != 202:
            return SendResult(success=False, error=f"SendGrid returned {response.status_code}: {response.text[:300]}")

        return SendResult(success=True, external_id=response.headers.get("X-Message-Id"))
