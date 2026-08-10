"""
Template models
"""

from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base
from app.models.tenant_base import TenantBase


class Template(TenantBase, Base):
    """Notification template model"""
    __tablename__ = "templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Template details
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(String(500), nullable=True)
    
    # Content
    subject = Column(String(500), nullable=True)
    body = Column(Text, nullable=False)
    
    # Configuration
    channels = Column(JSON, nullable=False)  # List of channels
    variables = Column(JSON, nullable=True)  # List of variable names
    default_priority = Column(String(20), default="info")
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Usage tracking
    usage_count = Column(Integer, default=0)
    last_used_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    notifications = relationship("Notification", back_populates="template")
    
    def __repr__(self):
        return f"<Template {self.name}>"
