"""
Real outbound delivery clients, one per NotificationChannel.

Shared shape across all of them (matches marketing-automation-engine's
app/services/esp/sendgrid_client.py, the fleet's existing pattern for
this): a `configured` property gate, a plain httpx POST to the provider's
real REST/webhook API, and an honest SendResult(success, error) - never a
fabricated success when the channel isn't configured or the provider
call fails.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class SendResult:
    success: bool
    error: Optional[str] = None
    external_id: Optional[str] = None
