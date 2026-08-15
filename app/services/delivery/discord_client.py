"""
Real Discord delivery via a webhook (https://discord.com/developers/docs/resources/webhook#execute-webhook).
A plain POST of a JSON payload to a per-channel webhook URL, no SDK needed.
"""

import httpx
from loguru import logger

from app.config import settings
from app.services.delivery import SendResult


class DiscordClient:
    def __init__(self):
        self.webhook_url = settings.discord_webhook_url

    @property
    def configured(self) -> bool:
        return bool(self.webhook_url)

    async def send(self, message: str) -> SendResult:
        if not self.configured:
            return SendResult(success=False, error="Discord is not configured (DISCORD_WEBHOOK_URL)")

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(self.webhook_url, json={"content": message})
        except httpx.HTTPError as exc:
            logger.error(f"Discord webhook request failed: {exc}")
            return SendResult(success=False, error=f"Discord webhook request failed: {exc}")

        if response.status_code not in (200, 204):
            return SendResult(success=False, error=f"Discord webhook returned {response.status_code}: {response.text[:300]}")

        return SendResult(success=True)
