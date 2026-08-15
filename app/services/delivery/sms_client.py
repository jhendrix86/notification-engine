"""
Real SMS delivery via Twilio's Messages API (raw httpx, not the twilio
SDK package - same convention as email_client.py).

https://www.twilio.com/docs/sms/api/message-resource#create-a-message-resource
"""

import httpx
from loguru import logger

from app.config import settings
from app.services.delivery import SendResult


class SmsClient:
    def __init__(self):
        self.account_sid = settings.twilio_account_sid
        self.auth_token = settings.twilio_auth_token
        self.from_number = settings.twilio_phone_number

    @property
    def configured(self) -> bool:
        return bool(self.account_sid and self.auth_token and self.from_number)

    async def send(self, to_number: str, message: str) -> SendResult:
        if not self.configured:
            return SendResult(
                success=False,
                error="Twilio is not configured (TWILIO_ACCOUNT_SID/TWILIO_AUTH_TOKEN/TWILIO_PHONE_NUMBER)",
            )

        url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    url,
                    auth=(self.account_sid, self.auth_token),
                    data={"To": to_number, "From": self.from_number, "Body": message},
                )
        except httpx.HTTPError as exc:
            logger.error(f"Twilio request failed: {exc}")
            return SendResult(success=False, error=f"Twilio request failed: {exc}")

        if response.status_code not in (200, 201):
            return SendResult(success=False, error=f"Twilio returned {response.status_code}: {response.text[:300]}")

        return SendResult(success=True, external_id=response.json().get("sid"))
