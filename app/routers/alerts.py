"""
Alert router - real DB-backed CRUD against the alerts table.
"""

import json
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from loguru import logger

from app.database import get_db
from app.models.alert import Alert, AlertPriority, AlertStatus
from app.models.tenant_base import apply_tenant_context

router = APIRouter()


class CreateAlertRequest(BaseModel):
    """Request to create alert"""
    source: str
    alert_type: str
    priority: AlertPriority = AlertPriority.INFO
    title: str
    description: Optional[str] = None
    metadata: Optional[dict] = None


class ResolveAlertRequest(BaseModel):
    """Request to resolve alert"""
    resolved_by: str
    resolution_notes: Optional[str] = None


class EscalateAlertRequest(BaseModel):
    """Request to escalate alert"""
    escalated_to: str
    escalation_notes: Optional[str] = None


def _serialize(alert: Alert) -> dict:
    return {
        "id": str(alert.id),
        "source": alert.source,
        "alert_type": alert.alert_type,
        "priority": alert.priority.value,
        "status": alert.status.value,
        "title": alert.title,
        "description": alert.description,
        "metadata": json.loads(alert.extra_metadata) if alert.extra_metadata else None,
        "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
        "resolved_by": alert.resolved_by,
        "resolution_notes": alert.resolution_notes,
        "escalated_at": alert.escalated_at.isoformat() if alert.escalated_at else None,
        "escalated_to": alert.escalated_to,
        "escalation_level": alert.escalation_level,
        "notification_count": alert.notification_count,
        "last_notification_at": alert.last_notification_at.isoformat() if alert.last_notification_at else None,
        "created_at": alert.created_at.isoformat(),
    }


async def _get_alert_or_404(db: AsyncSession, alert_id: str) -> Alert:
    try:
        alert_uuid = uuid.UUID(alert_id)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Alert '{alert_id}' not found")

    alert = await db.get(Alert, alert_uuid)
    if alert is None:
        raise HTTPException(status_code=404, detail=f"Alert '{alert_id}' not found")
    return alert


@router.post("/create")
async def create_alert(request: CreateAlertRequest, db: AsyncSession = Depends(get_db)):
    """Create an alert"""
    try:
        logger.info(f"Creating alert from {request.source}: {request.title}")

        alert = Alert(
            source=request.source,
            alert_type=request.alert_type,
            priority=request.priority,
            status=AlertStatus.OPEN,
            title=request.title,
            description=request.description,
            extra_metadata=json.dumps(request.metadata) if request.metadata else None,
        )
        apply_tenant_context(alert)

        db.add(alert)
        await db.commit()
        await db.refresh(alert)

        logger.info(f"Alert created: {alert.id}")
        return _serialize(alert)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{alert_id}/resolve")
async def resolve_alert(alert_id: str, request: ResolveAlertRequest, db: AsyncSession = Depends(get_db)):
    """Resolve an alert"""
    try:
        alert = await _get_alert_or_404(db, alert_id)

        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = datetime.utcnow()
        alert.resolved_by = request.resolved_by
        alert.resolution_notes = request.resolution_notes

        await db.commit()
        await db.refresh(alert)

        logger.info(f"Alert resolved: {alert_id}")
        return _serialize(alert)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to resolve alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{alert_id}/escalate")
async def escalate_alert(alert_id: str, request: EscalateAlertRequest, db: AsyncSession = Depends(get_db)):
    """Escalate an alert"""
    try:
        alert = await _get_alert_or_404(db, alert_id)

        alert.status = AlertStatus.ESCALATED
        alert.escalated_at = datetime.utcnow()
        alert.escalated_to = request.escalated_to
        alert.escalation_level = (alert.escalation_level or 0) + 1
        if request.escalation_notes:
            alert.resolution_notes = request.escalation_notes

        await db.commit()
        await db.refresh(alert)

        logger.info(f"Alert escalated: {alert_id}")
        return _serialize(alert)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to escalate alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{alert_id}")
async def get_alert(alert_id: str, db: AsyncSession = Depends(get_db)):
    """Get alert details"""
    try:
        alert = await _get_alert_or_404(db, alert_id)
        return _serialize(alert)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_alerts(
    status: Optional[AlertStatus] = None,
    priority: Optional[AlertPriority] = None,
    source: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """List all alerts, real filters applied against the database"""
    try:
        query = select(Alert)
        if status is not None:
            query = query.where(Alert.status == status)
        if priority is not None:
            query = query.where(Alert.priority == priority)
        if source is not None:
            query = query.where(Alert.source == source)

        query = query.order_by(Alert.created_at.desc()).offset(offset).limit(limit)

        result = await db.execute(query)
        alerts = result.scalars().all()

        return {
            "total": len(alerts),
            "alerts": [_serialize(a) for a in alerts],
            "filters": {
                "status": status.value if status else None,
                "priority": priority.value if priority else None,
                "source": source,
            },
            "pagination": {"limit": limit, "offset": offset},
        }

    except Exception as e:
        logger.error(f"Failed to list alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))
