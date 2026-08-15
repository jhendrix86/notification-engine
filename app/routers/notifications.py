"""
Notification router - real DB-backed CRUD plus real outbound delivery
(app/services/delivery) against the primary requested channel.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel
from loguru import logger

from app.database import get_db
from app.models.alert import Alert
from app.models.notification import Notification, NotificationStatus, NotificationChannel
from app.models.template import Template
from app.models.tenant_base import apply_tenant_context
from app.services.delivery.dispatch import deliver

router = APIRouter()


class SendNotificationRequest(BaseModel):
    """Request to send a notification. Requires either `message` or `template_id`."""
    recipient: str
    recipient_type: str = "email"
    channels: List[NotificationChannel]
    subject: Optional[str] = None
    message: Optional[str] = None
    data: Optional[dict] = None
    template_id: Optional[str] = None
    alert_id: Optional[str] = None


class BatchNotificationRequest(BaseModel):
    """Request to send the same content to multiple recipients"""
    recipients: List[str]
    recipient_type: str = "email"
    channels: List[NotificationChannel]
    subject: Optional[str] = None
    message: Optional[str] = None
    data: Optional[dict] = None
    template_id: Optional[str] = None


class _MissingAsBraces(dict):
    """Lets template rendering leave an unknown {variable} in place instead of raising."""
    def __missing__(self, key):
        return "{" + key + "}"


def _render(text: Optional[str], data: dict) -> Optional[str]:
    if text is None:
        return None
    return text.format_map(_MissingAsBraces(data or {}))


def _serialize(n: Notification) -> dict:
    return {
        "id": str(n.id),
        "alert_id": str(n.alert_id) if n.alert_id else None,
        "template_id": str(n.template_id) if n.template_id else None,
        "recipient": n.recipient,
        "recipient_type": n.recipient_type,
        "channels": n.channels,
        "primary_channel": n.primary_channel.value,
        "subject": n.subject,
        "message": n.message,
        "data": n.data,
        "status": n.status.value,
        "sent_at": n.sent_at.isoformat() if n.sent_at else None,
        "delivered_at": n.delivered_at.isoformat() if n.delivered_at else None,
        "failed_at": n.failed_at.isoformat() if n.failed_at else None,
        "error_message": n.error_message,
        "retry_count": n.retry_count,
        "max_retries": n.max_retries,
        "external_id": n.external_id,
        "created_at": n.created_at.isoformat(),
    }


async def _get_notification_or_404(db: AsyncSession, notification_id: str) -> Notification:
    try:
        notif_uuid = uuid.UUID(notification_id)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Notification '{notification_id}' not found")

    notification = await db.get(Notification, notif_uuid)
    if notification is None:
        raise HTTPException(status_code=404, detail=f"Notification '{notification_id}' not found")
    return notification


async def _resolve_template(db: AsyncSession, template_id: Optional[str]) -> Optional[Template]:
    if not template_id:
        return None
    try:
        template_uuid = uuid.UUID(template_id)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Template '{template_id}' not found")

    template = await db.get(Template, template_uuid)
    if template is None:
        raise HTTPException(status_code=404, detail=f"Template '{template_id}' not found")
    return template


async def _resolve_alert(db: AsyncSession, alert_id: Optional[str]) -> Optional[Alert]:
    if not alert_id:
        return None
    try:
        alert_uuid = uuid.UUID(alert_id)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Alert '{alert_id}' not found")

    alert = await db.get(Alert, alert_uuid)
    if alert is None:
        raise HTTPException(status_code=404, detail=f"Alert '{alert_id}' not found")
    return alert


async def _resolve_content(db: AsyncSession, template: Optional[Template], subject: Optional[str], message: Optional[str], data: Optional[dict]):
    if template is not None:
        data = data or {}
        if subject is None:
            subject = _render(template.subject, data)
        if message is None:
            message = _render(template.body, data)
        template.usage_count = (template.usage_count or 0) + 1
        template.last_used_at = datetime.utcnow()

    if message is None:
        raise HTTPException(status_code=400, detail="Either 'message' or 'template_id' must be provided")

    return subject, message


async def _create_and_deliver(
    db: AsyncSession,
    recipient: str,
    recipient_type: str,
    channels: List[NotificationChannel],
    subject: Optional[str],
    message: str,
    data: Optional[dict],
    template: Optional[Template],
    alert: Optional[Alert],
) -> Notification:
    primary_channel = channels[0]

    notification = Notification(
        alert_id=alert.id if alert else None,
        template_id=template.id if template else None,
        recipient=recipient,
        recipient_type=recipient_type,
        channels=[c.value for c in channels],
        primary_channel=primary_channel,
        subject=subject,
        message=message,
        data=data,
        status=NotificationStatus.PENDING,
    )
    apply_tenant_context(notification)
    db.add(notification)
    await db.flush()

    result = await deliver(primary_channel, recipient, subject or "", message)

    if result.success:
        notification.status = NotificationStatus.SENT
        notification.sent_at = datetime.utcnow()
        notification.external_id = result.external_id
    else:
        notification.status = NotificationStatus.FAILED
        notification.failed_at = datetime.utcnow()
        notification.error_message = result.error

    if alert is not None:
        alert.notification_count = (alert.notification_count or 0) + 1
        alert.last_notification_at = datetime.utcnow()

    return notification


@router.post("/send")
async def send_notification(request: SendNotificationRequest, db: AsyncSession = Depends(get_db)):
    """Send a notification - real delivery attempted on the primary (first) requested channel"""
    try:
        if not request.channels:
            raise HTTPException(status_code=400, detail="At least one channel is required")

        logger.info(f"Sending notification to {request.recipient} via {request.channels[0].value}")

        template = await _resolve_template(db, request.template_id)
        alert = await _resolve_alert(db, request.alert_id)
        subject, message = await _resolve_content(db, template, request.subject, request.message, request.data)

        notification = await _create_and_deliver(
            db, request.recipient, request.recipient_type, request.channels,
            subject, message, request.data, template, alert,
        )

        await db.commit()
        await db.refresh(notification)

        logger.info(f"Notification {notification.status.value}: {notification.id}")
        return _serialize(notification)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch")
async def send_batch_notifications(request: BatchNotificationRequest, db: AsyncSession = Depends(get_db)):
    """Send the same content to multiple recipients - real delivery attempted per recipient"""
    try:
        if not request.channels:
            raise HTTPException(status_code=400, detail="At least one channel is required")
        if not request.recipients:
            raise HTTPException(status_code=400, detail="At least one recipient is required")

        logger.info(f"Sending batch notifications to {len(request.recipients)} recipients")

        template = await _resolve_template(db, request.template_id)
        subject, message = await _resolve_content(db, template, request.subject, request.message, request.data)

        notifications = []
        for recipient in request.recipients:
            notification = await _create_and_deliver(
                db, recipient, request.recipient_type, request.channels,
                subject, message, request.data, template, alert=None,
            )
            notifications.append(notification)

        await db.commit()
        for n in notifications:
            await db.refresh(n)

        sent = sum(1 for n in notifications if n.status == NotificationStatus.SENT)
        logger.info(f"Batch notifications: {sent}/{len(notifications)} sent")

        return {
            "total": len(notifications),
            "sent": sent,
            "failed": len(notifications) - sent,
            "notifications": [_serialize(n) for n in notifications],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send batch notifications: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{notification_id}")
async def get_notification(notification_id: str, db: AsyncSession = Depends(get_db)):
    """Get notification details"""
    try:
        notification = await _get_notification_or_404(db, notification_id)
        return _serialize(notification)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_notifications(
    status: Optional[NotificationStatus] = None,
    recipient: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """List notifications, real filters applied against the database"""
    try:
        query = select(Notification)
        if status is not None:
            query = query.where(Notification.status == status)
        if recipient is not None:
            query = query.where(Notification.recipient == recipient)

        query = query.order_by(Notification.created_at.desc()).offset(offset).limit(limit)

        result = await db.execute(query)
        notifications = result.scalars().all()

        return {
            "total": len(notifications),
            "notifications": [_serialize(n) for n in notifications],
            "filters": {"status": status.value if status else None, "recipient": recipient},
            "pagination": {"limit": limit, "offset": offset},
        }

    except Exception as e:
        logger.error(f"Failed to list notifications: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{notification_id}/retry")
async def retry_notification(notification_id: str, db: AsyncSession = Depends(get_db)):
    """Retry a notification - real re-delivery attempt on its primary channel"""
    try:
        notification = await _get_notification_or_404(db, notification_id)

        notification.retry_count = (notification.retry_count or 0) + 1
        notification.status = NotificationStatus.RETRYING
        await db.flush()

        result = await deliver(notification.primary_channel, notification.recipient, notification.subject or "", notification.message)

        if result.success:
            notification.status = NotificationStatus.SENT
            notification.sent_at = datetime.utcnow()
            notification.external_id = result.external_id
            notification.error_message = None
        else:
            notification.status = NotificationStatus.FAILED
            notification.failed_at = datetime.utcnow()
            notification.error_message = result.error

        await db.commit()
        await db.refresh(notification)

        logger.info(f"Notification retry {notification.status.value}: {notification_id}")
        return _serialize(notification)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retry notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))
