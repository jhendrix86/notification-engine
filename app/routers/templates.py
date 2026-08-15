"""
Notification templates router - real DB-backed CRUD against the
templates table.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from pydantic import BaseModel
from loguru import logger

from app.database import get_db
from app.models.template import Template
from app.models.tenant_base import apply_tenant_context

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


class UpdateTemplateRequest(BaseModel):
    """Request to update a notification template - all fields optional"""
    body: Optional[str] = None
    subject: Optional[str] = None
    description: Optional[str] = None
    channels: Optional[List[str]] = None
    variables: Optional[List[str]] = None
    is_active: Optional[bool] = None


def _serialize(template: Template) -> dict:
    return {
        "id": str(template.id),
        "name": template.name,
        "description": template.description,
        "subject": template.subject,
        "body": template.body,
        "channels": template.channels,
        "variables": template.variables,
        "default_priority": template.default_priority,
        "is_active": template.is_active,
        "usage_count": template.usage_count,
        "last_used_at": template.last_used_at.isoformat() if template.last_used_at else None,
        "created_at": template.created_at.isoformat(),
    }


async def _get_template_or_404(db: AsyncSession, template_id: str) -> Template:
    try:
        template_uuid = uuid.UUID(template_id)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Template '{template_id}' not found")

    template = await db.get(Template, template_uuid)
    if template is None:
        raise HTTPException(status_code=404, detail=f"Template '{template_id}' not found")
    return template


@router.post("/create")
async def create_template(request: CreateTemplateRequest, db: AsyncSession = Depends(get_db)):
    """Create a notification template"""
    try:
        logger.info(f"Creating template: {request.name}")

        template = Template(
            name=request.name,
            description=request.description,
            subject=request.subject,
            body=request.body,
            channels=request.channels,
            variables=request.variables,
            default_priority=request.default_priority,
        )
        apply_tenant_context(template)

        db.add(template)
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            raise HTTPException(status_code=409, detail=f"A template named '{request.name}' already exists")
        await db.refresh(template)

        logger.info(f"Template created: {template.id}")
        return _serialize(template)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{template_id}")
async def get_template(template_id: str, db: AsyncSession = Depends(get_db)):
    """Get template details"""
    try:
        template = await _get_template_or_404(db, template_id)
        return _serialize(template)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{template_id}")
async def update_template(template_id: str, request: UpdateTemplateRequest, db: AsyncSession = Depends(get_db)):
    """Update a notification template"""
    try:
        template = await _get_template_or_404(db, template_id)

        for field, value in request.model_dump(exclude_unset=True).items():
            setattr(template, field, value)

        await db.commit()
        await db.refresh(template)

        return _serialize(template)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_templates(
    is_active: Optional[bool] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """List notification templates, real filters applied against the database"""
    try:
        query = select(Template)
        if is_active is not None:
            query = query.where(Template.is_active == is_active)

        query = query.order_by(Template.created_at.desc()).offset(offset).limit(limit)

        result = await db.execute(query)
        templates = result.scalars().all()

        return {
            "total": len(templates),
            "templates": [_serialize(t) for t in templates],
            "filters": {"is_active": is_active},
            "pagination": {"limit": limit, "offset": offset},
        }

    except Exception as e:
        logger.error(f"Failed to list templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))
