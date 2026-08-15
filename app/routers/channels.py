"""
Channel router - real DB-backed CRUD against the channels table, and
/test actually attempts real delivery through app/services/delivery.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from loguru import logger

from app.database import get_db
from app.models.channel import Channel, ChannelStatus
from app.models.notification import NotificationChannel
from app.models.tenant_base import apply_tenant_context
from app.services.delivery.dispatch import deliver

router = APIRouter()


class TestChannelRequest(BaseModel):
    """Request to test channel"""
    channel_type: str
    test_message: str = "Test notification from Notification Engine"
    recipient: Optional[str] = None  # required for email/sms/webhook; ignored for slack/discord


class ConfigureChannelRequest(BaseModel):
    """Request to configure channel"""
    channel_type: str
    config: dict
    credentials: Optional[dict] = None


def _serialize(channel: Channel) -> dict:
    return {
        "id": str(channel.id),
        "channel_type": channel.channel_type,
        "name": channel.name,
        "description": channel.description,
        "config": channel.config,
        "status": channel.status.value,
        "rate_limit_per_minute": channel.rate_limit_per_minute,
        "rate_limit_per_hour": channel.rate_limit_per_hour,
        "last_health_check": channel.last_health_check.isoformat() if channel.last_health_check else None,
        "last_error": channel.last_error,
        "error_count": channel.error_count,
    }


def _parse_channel_type(channel_type: str) -> NotificationChannel:
    try:
        return NotificationChannel(channel_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unknown channel type '{channel_type}'")


async def _get_or_create_channel(db: AsyncSession, channel_type: NotificationChannel) -> Channel:
    result = await db.execute(select(Channel).where(Channel.channel_type == channel_type.value))
    channel = result.scalar_one_or_none()
    if channel is None:
        channel = Channel(channel_type=channel_type.value, name=channel_type.value.capitalize(), config={})
        apply_tenant_context(channel)
        db.add(channel)
        await db.flush()
    return channel


@router.post("/test")
async def test_channel(request: TestChannelRequest, db: AsyncSession = Depends(get_db)):
    """Test a notification channel - a real delivery attempt, not a simulated success"""
    try:
        channel_type = _parse_channel_type(request.channel_type)
        logger.info(f"Testing channel: {channel_type.value}")

        channel = await _get_or_create_channel(db, channel_type)

        result = await deliver(channel_type, request.recipient or "", "Notification Engine test", request.test_message)

        channel.last_health_check = datetime.utcnow()
        if result.success:
            channel.status = ChannelStatus.ACTIVE
            channel.last_error = None
        else:
            channel.status = ChannelStatus.ERROR
            channel.last_error = result.error
            channel.error_count = (channel.error_count or 0) + 1

        await db.commit()
        await db.refresh(channel)

        logger.info(f"Channel test {'succeeded' if result.success else 'failed'}: {channel_type.value}")
        return {
            "channel_type": channel_type.value,
            "status": "success" if result.success else "failed",
            "error": result.error,
            "external_id": result.external_id,
            "tested_at": channel.last_health_check.isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to test channel: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_channel_status(db: AsyncSession = Depends(get_db)):
    """Get status of every channel that's been configured or tested at least once"""
    try:
        result = await db.execute(select(Channel).order_by(Channel.channel_type))
        channels = result.scalars().all()

        return {"total": len(channels), "channels": [_serialize(c) for c in channels]}

    except Exception as e:
        logger.error(f"Failed to get channel status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/configure")
async def configure_channel(request: ConfigureChannelRequest, db: AsyncSession = Depends(get_db)):
    """Configure a channel - persists real config/credentials, no delivery attempted"""
    try:
        channel_type = _parse_channel_type(request.channel_type)
        logger.info(f"Configuring channel: {channel_type.value}")

        channel = await _get_or_create_channel(db, channel_type)
        channel.config = request.config
        if request.credentials is not None:
            channel.credentials = request.credentials
        channel.status = ChannelStatus.ACTIVE

        await db.commit()
        await db.refresh(channel)

        logger.info(f"Channel configured: {channel_type.value}")
        return _serialize(channel)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to configure channel: {e}")
        raise HTTPException(status_code=500, detail=str(e))
