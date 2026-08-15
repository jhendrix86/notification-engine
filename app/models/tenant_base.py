"""
Tenant base mixin for multi-tenancy support
"""

from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declared_attr
from loguru import logger

from app.tenant_context import get_tenant_context


class TenantBase:
    """Mixin class that adds tenant_id to models for multi-tenancy."""

    @declared_attr
    def tenant_id(cls):
        return Column(
            UUID(as_uuid=True),
            ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=True,  # Initially nullable for migration
            index=True,
            comment="Tenant identifier for data isolation"
        )


def apply_tenant_context(model_instance):
    """
    Apply the current request's tenant context to a model instance, if one
    is set and the instance doesn't already have a tenant_id.
    """
    tenant_id = get_tenant_context()

    if tenant_id is None:
        logger.debug("No tenant context available, skipping tenant assignment")
        return

    if hasattr(model_instance, "tenant_id") and model_instance.tenant_id is None:
        model_instance.tenant_id = tenant_id
        logger.debug(f"Applied tenant context to model: {tenant_id}")
