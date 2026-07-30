"""
Notification router
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel
from loguru import logger

from app.database import get_db
from app.models.notification import Notification, NotificationStatus, NotificationChannel

router = APIRouter()


class SendNotificationRequest(BaseModel):
    """Request to send notification"""
    recipient: str
    channels: List[str]
    priority: str = "info"
    subject: Optional[str] = None
    message: str
    data: Optional[dict] = None
    template_id: Optional[str] = None


class BatchNotificationRequest(BaseModel):
    """Request to send batch notifications"""
    recipients: List[str]
    channels: List[str]
    priority: str = "info"
    subject: Optional[str] = None
    message: str
    data: Optional[dict] = None


@router.post("/send")
async def send_notification(
    request: SendNotificationRequest,
    db: AsyncSession = Depends(get_db)
):
    """Send a notification"""
    try:
        logger.info(f"Sending notification to {request.recipient}")
        
        # In production, this would save to database and dispatch to channels
        # For now, return a mock response
        notification = {
            "id": "notif_123",
            "recipient": request.recipient,
            "channels": request.channels,
            "primary_channel": request.channels[0],
            "subject": request.subject,
            "message": request.message,
            "status": "sent",
            "sent_at": datetime.utcnow isoformat(),
            "external_id": "ext_123"
        }
        
        logger.info(f"Notification sent: {notification['id']}")
        return notification
        
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch")
async def send_batch_notifications(
    request: BatchNotificationRequest,
    db: AsyncSession = Depends(get_db)
):
    """Send batch notifications"""
    try:
        logger.info(f"Sending batch notifications to {len(request.recipients)} recipients")
        
        # In production, this would create notifications for each recipient
        # For now, return a mock response
        notifications = [
            {
                "id": f"notif_{i}",
                "recipient": recipient,
                "status": "sent",
                "sent_at": datetime.utcnow().isoformat()
            }
            for i, recipient in enumerate(request.recipients)
        ]
        
        logger.info(f"Batch notifications sent: {len(notifications)}")
        return {
            "total": len(notifications),
            "notifications": notifications,
            "status": "completed"
        }
        
    except Exception as e:
        logger.error(f"Failed to send batch notifications: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{notification_id}")
async def get_notification(
    notification_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get notification details"""
    try:
        logger.info(f"Getting notification details for {notification_id}")
        
        # In production, this would query from database
        # For now, return a mock response
        notification = {
            "id": notification_id,
            "recipient": "user@example.com",
            "channels": ["email", "slack"],
            "primary_channel": "email",
            "subject": "System Alert",
            "message": "Payment processing failed",
            "status": "sent",
            "sent_at": datetime.utcnow().isoformat(),
            "external_id": "ext_123"
        }
        
        return notification
        
    except Exception as e:
        logger.error(f"Failed to get notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_notifications(
    status: Optional[str] = None,
    recipient: Optional[str] = None,
    channel: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """List notifications"""
    try:
        logger.info("Listing notifications")
        
        # In production, this would query from database with filters
        # For now, return a mock response
        notifications = [
            {
                "id": "notif_001",
                "recipient": "user@example.com",
                "channels": ["email"],
                "status": "sent",
                "sent_at": datetime.utcnow().isoformat()
            },
            {
                "id": "notif_002",
                "recipient": "admin@example.com",
                "channels": ["slack"],
                "status": "sent",
                "sent_at": (datetime.utcnow() - timedelta(hours=1)).isoformat()
            }
        ]
        
        return {
            "total": len(notifications),
            "notifications": notifications,
            "filters": {
                "status": status,
                "recipient": recipient,
                "channel": channel
            },
            "pagination": {
                "limit": limit,
                "offset": offset
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to list notifications: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{notification_id}/retry")
async def retry_notification(
    notification_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Retry a failed notification"""
    try:
        logger.info(f"Retrying notification {notification_id}")
        
        # In production, this would update status and redeliver
        # For now, return a mock response
        notification = {
            "id": notification_id,
            "status": "retrying",
            "retry_count": 1,
            "retried_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Notification retry initiated: {notification_id}")
        return notification
        
    except Exception as e:
        logger.error(f"Failed to retry notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))
