"""
Notification templates router
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel
from loguru import logger

from app.database import get_db

router = APIRouter()


class CreateTemplateRequest(BaseModel):
    """Request to create a notification template"""
    name: str
    description: Optional[str] = None
    subject: Optional[str] = None
    body: str
    channels: List[str]
    variables: Optional[List[str]] = None
    default_priority: Optional[str] = "info"


@router.post("/create")
async def create_template(
    request: CreateTemplateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create a notification template"""
    try:
        logger.info(f"Creating template: {request.name}")

        # In production, this would save to database
        # For now, return a mock response
        template = {
            "id": "template_123",
            "name": request.name,
            "description": request.description,
            "subject": request.subject,
            "body": request.body,
            "channels": request.channels,
            "variables": request.variables,
            "default_priority": request.default_priority,
            "is_active": True,
            "usage_count": 0,
            "created_at": datetime.utcnow().isoformat()
        }

        logger.info(f"Template created: {template['id']}")
        return template

    except Exception as e:
        logger.error(f"Failed to create template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{template_id}")
async def get_template(template_id: str, db: AsyncSession = Depends(get_db)):
    """Get template details"""
    try:
        logger.info(f"Getting template details for {template_id}")

        # In production, this would query from database
        # For now, return a mock response
        template = {
            "id": template_id,
            "name": "payment_failed",
            "subject": "Payment Failed",
            "body": "Your payment of {{amount}} could not be processed.",
            "channels": ["email", "slack"],
            "variables": ["amount"],
            "is_active": True,
            "usage_count": 42,
            "created_at": datetime.utcnow().isoformat()
        }

        return template

    except Exception as e:
        logger.error(f"Failed to get template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{template_id}")
async def update_template(
    template_id: str,
    body: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db)
):
    """Update a notification template"""
    try:
        logger.info(f"Updating template {template_id}")

        # In production, this would update database
        # For now, return a mock response
        template = {
            "id": template_id,
            "body": body,
            "is_active": is_active,
            "updated_at": datetime.utcnow().isoformat()
        }

        return template

    except Exception as e:
        logger.error(f"Failed to update template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_templates(
    is_active: Optional[bool] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """List notification templates"""
    try:
        logger.info("Listing templates")

        # In production, this would query from database with filters
        # For now, return a mock response
        templates = [
            {"id": "template_001", "name": "payment_failed", "channels": ["email", "slack"], "is_active": True},
            {"id": "template_002", "name": "welcome", "channels": ["email"], "is_active": True},
        ]

        return {
            "total": len(templates),
            "templates": templates,
            "filters": {"is_active": is_active},
            "pagination": {"limit": limit, "offset": offset}
        }

    except Exception as e:
        logger.error(f"Failed to list templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))
