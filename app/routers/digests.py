"""
Digest router
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
from loguru import logger

from app.database import get_db

router = APIRouter()


class CreateDigestRequest(BaseModel):
    """Request to create digest"""
    name: str
    description: Optional[str] = None
    schedule: str = "daily"
    recipients: list
    channels: list
    priority_filter: Optional[list] = None
    source_filter: Optional[list] = None


@router.post("/create")
async def create_digest(
    request: CreateDigestRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create a digest schedule"""
    try:
        logger.info(f"Creating digest: {request.name}")
        
        # Calculate next send time based on schedule
        if request.schedule == "daily":
            next_send = datetime.utcnow() + timedelta(days=1)
        elif request.schedule == "weekly":
            next_send = datetime.utcnow() + timedelta(weeks=1)
        elif request.schedule == "hourly":
            next_send = datetime.utcnow() + timedelta(hours=1)
        else:
            next_send = datetime.utcnow() + timedelta(hours=6)
        
        # In production, this would save to database
        # For now, return a mock response
        digest = {
            "id": "digest_123",
            "name": request.name,
            "description": request.description,
            "schedule": request.schedule,
            "recipients": request.recipients,
            "channels": request.channels,
            "priority_filter": request.priority_filter,
            "source_filter": request.source_filter,
            "is_active": True,
            "next_send_at": next_send.isoformat(),
            "created_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Digest created: {digest['id']}")
        return digest
        
    except Exception as e:
        logger.error(f"Failed to create digest: {e}")
        raise HTTPException(status_code=500, detail(str(e))


@router.get("/{digest_id}")
async def get_digest(
    digest_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get digest details"""
    try:
        logger.info(f"Getting digest details for {digest_id}")
        
        # In production, this would query from database
        # For now, return a mock response
        digest = {
            "id": digest_id,
            "name": "Daily Critical Alerts",
            "description": "Daily digest of critical alerts",
            "schedule": "daily",
            "recipients": ["admin@example.com"],
            "channels": ["email"],
            "is_active": True,
            "last_sent_at": (datetime.utcnow() - timedelta(days=1)).isoformat(),
            "next_send_at": (datetime.utcnow() + timedelta(hours=12)).isoformat(),
            "pending_notifications": 3
        }
        
        return digest
        
    except Exception as e:
        logger.error(f"Failed to get digest: {e}")
        raise HTTPException(status_code=500, detail(str(e))


@router.post("/{digest_id}/send")
async def send_digest(
    digest_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Send digest immediately"""
    try:
        logger.info(f"Sending digest {digest_id} immediately")
        
        # In production, this would compile and send digest
        # For now, return a mock response
        digest = {
            "id": digest_id,
            "status": "sent",
            "sent_at": datetime.utcnow().isoformat(),
            "notifications_sent": 5,
            "recipients_notified": 1
        }
        
        logger.info(f"Digest sent: {digest_id}")
        return digest
        
    except Exception as e:
        logger.error(f"Failed to send digest: {e}")
        raise HTTPException(status_code=500, detail=str(e))
