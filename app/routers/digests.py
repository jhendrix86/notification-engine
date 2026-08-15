"""
Digest router - real DB-backed CRUD against the digests table.
POST /{id}/send compiles a real digest from actually-open Alert rows
(filtered per the digest's own priority/source filters) and dispatches
it to every recipient via the real delivery clients - not a simulated
notification count.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
from loguru import logger

from app.database import get_db
from app.models.alert import Alert, AlertStatus
from app.models.digest import Digest, DigestSchedule
from app.models.notification import NotificationChannel
from app.models.tenant_base import apply_tenant_context
from app.services.delivery.dispatch import deliver

router = APIRouter()

_OPEN_STATUSES = [AlertStatus.OPEN, AlertStatus.IN_PROGRESS, AlertStatus.ESCALATED]


class CreateDigestRequest(BaseModel):
    """Request to create digest"""
    name: str
    description: Optional[str] = None
    schedule: DigestSchedule = DigestSchedule.DAILY
    recipients: list
    channels: list
    priority_filter: Optional[list] = None
    source_filter: Optional[list] = None


def _next_send_time(schedule: DigestSchedule, base: datetime) -> datetime:
    if schedule == DigestSchedule.DAILY:
        return base + timedelta(days=1)
    if schedule == DigestSchedule.WEEKLY:
        return base + timedelta(weeks=1)
    if schedule == DigestSchedule.HOURLY:
        return base + timedelta(hours=1)
    return base + timedelta(hours=6)  # custom - no schedule_config interpreter yet, safe default


def _serialize(digest: Digest) -> dict:
    return {
        "id": str(digest.id),
        "name": digest.name,
        "description": digest.description,
        "schedule": digest.schedule.value,
        "recipients": digest.recipients,
        "channels": digest.channels,
        "priority_filter": digest.priority_filter,
        "source_filter": digest.source_filter,
        "is_active": digest.is_active,
        "last_sent_at": digest.last_sent_at.isoformat() if digest.last_sent_at else None,
        "next_send_at": digest.next_send_at.isoformat() if digest.next_send_at else None,
        "created_at": digest.created_at.isoformat(),
    }


async def _get_digest_or_404(db: AsyncSession, digest_id: str) -> Digest:
    try:
        digest_uuid = uuid.UUID(digest_id)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Digest '{digest_id}' not found")

    digest = await db.get(Digest, digest_uuid)
    if digest is None:
        raise HTTPException(status_code=404, detail=f"Digest '{digest_id}' not found")
    return digest


async def _compile_digest_body(db: AsyncSession, digest: Digest) -> tuple[str, int]:
    """Real query of currently-open alerts matching this digest's own filters."""
    query = select(Alert).where(Alert.status.in_(_OPEN_STATUSES))
    if digest.priority_filter:
        query = query.where(Alert.priority.in_(digest.priority_filter))
    if digest.source_filter:
        query = query.where(Alert.source.in_(digest.source_filter))

    result = await db.execute(query.order_by(Alert.created_at.desc()))
    alerts = result.scalars().all()

    if not alerts:
        return "No open alerts matching this digest's filters.", 0

    lines = [f"- [{a.priority.value.upper()}] {a.title} ({a.source})" for a in alerts]
    return "\n".join(lines), len(alerts)


@router.post("/create")
async def create_digest(request: CreateDigestRequest, db: AsyncSession = Depends(get_db)):
    """Create a digest schedule"""
    try:
        logger.info(f"Creating digest: {request.name}")

        now = datetime.utcnow()
        digest = Digest(
            name=request.name,
            description=request.description,
            schedule=request.schedule,
            recipients=request.recipients,
            channels=request.channels,
            priority_filter=request.priority_filter,
            source_filter=request.source_filter,
            next_send_at=_next_send_time(request.schedule, now),
        )
        apply_tenant_context(digest)

        db.add(digest)
        await db.commit()
        await db.refresh(digest)

        logger.info(f"Digest created: {digest.id}")
        return _serialize(digest)

    except Exception as e:
        logger.error(f"Failed to create digest: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{digest_id}")
async def get_digest(digest_id: str, db: AsyncSession = Depends(get_db)):
    """Get digest details"""
    try:
        digest = await _get_digest_or_404(db, digest_id)
        return _serialize(digest)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get digest: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{digest_id}/send")
async def send_digest(digest_id: str, db: AsyncSession = Depends(get_db)):
    """Send digest immediately - a real compile-and-deliver pass, not a simulated count"""
    try:
        digest = await _get_digest_or_404(db, digest_id)

        if not digest.channels:
            raise HTTPException(status_code=400, detail="This digest has no channels configured")

        logger.info(f"Sending digest {digest_id} immediately")

        body, alert_count = await _compile_digest_body(db, digest)
        subject = f"Digest: {digest.name}"
        primary_channel = NotificationChannel(digest.channels[0])

        sent, failed = 0, 0
        for recipient in digest.recipients:
            result = await deliver(primary_channel, recipient, subject, body)
            if result.success:
                sent += 1
            else:
                failed += 1

        digest.last_sent_at = datetime.utcnow()
        digest.next_send_at = _next_send_time(digest.schedule, digest.last_sent_at)

        await db.commit()
        await db.refresh(digest)

        status = "sent" if failed == 0 else ("partial" if sent else "failed")
        logger.info(f"Digest {status}: {digest_id} ({sent} sent, {failed} failed)")

        return {
            "id": str(digest.id),
            "status": status,
            "sent_at": digest.last_sent_at.isoformat(),
            "alerts_included": alert_count,
            "recipients_notified": sent,
            "recipients_failed": failed,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send digest: {e}")
        raise HTTPException(status_code=500, detail=str(e))
