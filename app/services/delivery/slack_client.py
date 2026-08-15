"""
Real Slack delivery via an incoming webhook (https://api.slack.com/messaging/webhooks).
No slack-sdk dependency needed - an incoming webhook is a plain POST of
a JSON payload to a per-workspace URL.
"""

import httpx
from loguru import logger

from app.config import settings
from app.services.delivery import SendResult


class SlackClient:
    def __init__(self):
        self.webhook_url = settings.slack_webhook_url

    @property
    def configured(self) -> bool:
        return bool(self.webhook_url)

    async def send(self, message: str, channel: str = None) -> SendResult:
        if not self.configured:
            return SendResult(success=False, error="Slack is not configured (SLACK_WEBHOOK_URL)")

        payload = {"text": message}
        if channel:
            payload["channel"] = channel

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(self.webhook_url, json=payload)
        except httpx.HTTPError as exc:
            logger.error(f"Slack webhook request failed: {exc}")
            return SendResult(success=False, error=f"Slack webhook request failed: {exc}")

        if response.status_code != 200:
            return SendResult(success=False, error=f"Slack webhook returned {response.status_code}: {response.text[:300]}")

        return SendResult(success=True)
