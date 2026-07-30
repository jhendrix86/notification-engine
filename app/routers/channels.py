"""
Channel router
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
from loguru import logger

from app.database import get_db

router = APIRouter()


class TestChannelRequest(BaseModel):
    """Request to test channel"""
    channel_type: str
    test_message: str = "Test notification from Notification Engine"


class ConfigureChannelRequest(BaseModel):
    """Request to configure channel"""
    channel_type: str
    config: dict
    credentials: Optional[dict] = None


@router.post("/test")
async def test_channel(
    request: TestChannelRequest,
    db: AsyncSession = Depends(get_db)
):
    """Test a notification channel"""
    try:
        logger.info(f"Testing channel: {request.channel_type}")
        
        # In production, this would send a test notification through the channel
        # For now, return a mock response
        result = {
            "channel_type": request.channel_type,
            "status": "success",
            "message": "Test notification sent successfully",
            "sent_at": datetime.utcnow().isoformat(),
            "external_id": "test_123"
        }
        
        logger.info(f"Channel test successful: {request.channel_type}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to test channel: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_channel_status(
    db: AsyncSession = Depends(get_db)
):
    """Get status of all channels"""
    try:
        logger.info("Getting channel status")
        
        # In production, this would query from database
        # For now, return a mock response
        channels = [
            {
                "channel_type": "email",
                "name": "Email (SendGrid)",
                "status": "active",
                "last_health_check": datetime.utcnow().isoformat(),
                "error_count": 0
            },
            {
                "channel_type": "slack",
                "name": "Slack",
                "status": "active",
                "last_health_check": datetime.utcnow().isoformat(),
                "error_count": 0
            },
            {
                "channel_type": "sms",
                "name": "SMS (Twilio)",
                "status": "active",
                "last_health_check": (datetime.utcnow() - timedelta(minutes=5)).isoformat(),
                "error_count": 0
            },
            {
                "channel_type": "discord",
                "name": "Discord",
                "status": "inactive",
                "last_health_check": None,
                "error_count": 0
            }
        ]
        
        return {
            "total": len(channels),
            "channels": channels
        }
        
    except Exception as e:
        logger.error(f"Failed to get channel status: {e}")
        raise HTTPException(status_code=500, detail(str(e))


@router.post("/configure")
async def configure_channel(
    request: ConfigureChannelRequest,
    db: AsyncSession = Depends(get_db)
):
    """Configure a channel"""
    try:
        logger.info(f"Configuring channel: {request.channel_type}")
        
        # In production, this would update channel configuration in database
        # For now, return a mock response
        channel = {
            "channel_type": request.channel_type,
            "status": "active",
            "configured_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Channel configured: {request.channel_type}")
        return channel
        
    except Exception as e:
        logger.error(f"Failed to configure channel: {e}")
        raise HTTPException(status_code=500, detail(str(e))
