"""
Real generic webhook delivery - unlike the other channels, there's no
fleet-wide webhook URL to configure: the target URL IS the notification's
`recipient` field (recipient_type="webhook_url"), so nothing needs to be
declared in Settings.
"""

import httpx
from loguru import logger

from app.services.delivery import SendResult


class WebhookClient:
    @property
    def configured(self) -> bool:
        return True  # the target URL comes from the notification itself, not config

    async def send(self, url: str, payload: dict) -> SendResult:
        if not url:
            return SendResult(success=False, error="No webhook URL given (recipient field was empty)")

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(url, json=payload)
        except httpx.HTTPError as exc:
            logger.error(f"Webhook request failed: {exc}")
            return SendResult(success=False, error=f"Webhook request failed: {exc}")

        if not (200 <= response.status_code < 300):
            return SendResult(success=False, error=f"Webhook returned {response.status_code}: {response.text[:300]}")

        return SendResult(success=True)
