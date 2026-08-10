"""
Tenant base mixin for multi-tenancy support
"""

from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID


class TenantBase:
    """Mixin class that adds tenant_id to models for multi-tenancy."""
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Tenant identifier for data isolation"
    )
