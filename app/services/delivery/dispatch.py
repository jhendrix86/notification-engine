"""
Routes a single channel delivery attempt to the right real client.
"""

from app.models.notification import NotificationChannel
from app.services.delivery import SendResult
from app.services.delivery.discord_client import DiscordClient
from app.services.delivery.email_client import EmailClient
from app.services.delivery.slack_client import SlackClient
from app.services.delivery.sms_client import SmsClient
from app.services.delivery.webhook_client import WebhookClient


async def deliver(channel: NotificationChannel, recipient: str, subject: str, message: str) -> SendResult:
    """Attempt real delivery of one notification over one channel."""
    if channel == NotificationChannel.EMAIL:
        return await EmailClient().send(to_email=recipient, subject=subject, message=message)
    if channel == NotificationChannel.SMS:
        return await SmsClient().send(to_number=recipient, message=message)
    if channel == NotificationChannel.SLACK:
        return await SlackClient().send(message=message)
    if channel == NotificationChannel.DISCORD:
        return await DiscordClient().send(message=message)
    if channel == NotificationChannel.WEBHOOK:
        return await WebhookClient().send(url=recipient, payload={"subject": subject, "message": message})
    return SendResult(success=False, error=f"Unknown channel: {channel}")
