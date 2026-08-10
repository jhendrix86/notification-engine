"""
Alert router
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
from loguru import logger

from app.database import get_db
from app.models.alert import Alert, AlertPriority, AlertStatus

router = APIRouter()


class CreateAlertRequest(BaseModel):
    """Request to create alert"""
    source: str
    alert_type: str
    priority: str = "info"
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


@router.post("/create")
async def create_alert(
    request: CreateAlertRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create an alert"""
    try:
        logger.info(f"Creating alert from {request.source}: {request.title}")
        
        # In production, this would save to database and trigger notifications
        # For now, return a mock response
        alert = {
            "id": "alert_123",
            "source": request.source,
            "alert_type": request.alert_type,
            "priority": request.priority,
            "title": request.title,
            "description": request.description,
            "status": "open",
            "created_at": datetime.utcnow().isoformat(),
            "metadata": request.metadata
        }
        
        logger.info(f"Alert created: {alert['id']}")
        return alert
        
    except Exception as e:
        logger.error(f"Failed to create alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    request: ResolveAlertRequest,
    db: AsyncSession = Depends(get_db)
):
    """Resolve an alert"""
    try:
        logger.info(f"Resolving alert {alert_id}")
        
        # In production, this would update database and stop notifications
        # For now, return a mock response
        alert = {
            "id": alert_id,
            "status": "resolved",
            "resolved_at": datetime.utcnow().isoformat(),
            "resolved_by": request.resolved_by,
            "resolution_notes": request.resolution_notes
        }
        
        logger.info(f"Alert resolved: {alert_id}")
        return alert
        
    except Exception as e:
        logger.error(f"Failed to resolve alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{alert_id}/escalate")
async def escalate_alert(
    alert_id: str,
    request: EscalateAlertRequest,
    db: AsyncSession = Depends(get_db)
):
    """Escalate an alert"""
    try:
        logger.info(f"Escalating alert {alert_id} to {request.escalated_to}")
        
        # In production, this would update database and send escalated notifications
        # For now, return a mock response
        alert = {
            "id": alert_id,
            "status": "escalated",
            "escalated_at": datetime.utcnow().isoformat(),
            "escalated_to": request.escalated_to,
            "escalation_level": 1,
            "escalation_notes": request.escalation_notes
        }
        
        logger.info(f"Alert escalated: {alert_id}")
        return alert
        
    except Exception as e:
        logger.error(f"Failed to escalate alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{alert_id}")
async def get_alert(
    alert_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get alert details"""
    try:
        logger.info(f"Getting alert details for {alert_id}")
        
        # In production, this would query from database
        # For now, return a mock response
        alert = {
            "id": alert_id,
            "source": "revenue-operations",
            "alert_type": "payment_failed",
            "priority": "critical",
            "title": "Payment Processing Failed",
            "description": "Payment pay_123 failed to process",
            "status": "open",
            "created_at": datetime.utcnow().isoformat(),
            "notification_count": 2,
            "last_notification_at": datetime.utcnow().isoformat()
        }
        
        return alert
        
    except Exception as e:
        logger.error(f"Failed to get alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_alerts(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    source: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """List all alerts"""
    try:
        logger.info("Listing alerts")
        
        # In production, this would query from database with filters
        # For now, return a mock response
        alerts = [
            {
                "id": "alert_001",
                "source": "revenue-operations",
                "alert_type": "payment_failed",
                "priority": "critical",
                "title": "Payment Processing Failed",
                "status": "open",
                "created_at": datetime.utcnow().isoformat()
            },
            {
                "id": "alert_002",
                "source": "funnel-automation",
                "alert_type": "conversion_drop",
                "priority": "warning",
                "title": "Conversion Rate Drop",
                "status": "in_progress",
                "created_at": (datetime.utcnow() - timedelta(hours=2)).isoformat()
            }
        ]
        
        return {
            "total": len(alerts),
            "alerts": alerts,
            "filters": {
                "status": status,
                "priority": priority,
                "source": source
            },
            "pagination": {
                "limit": limit,
                "offset": offset
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to list alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))
