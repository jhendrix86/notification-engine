"""
Alert models
"""

from sqlalchemy import Column, String, Integer, DateTime, Boolean, Enum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base
from app.models.tenant_base import TenantBase


class AlertPriority(str, enum.Enum):
    """Alert priority enumeration"""
    CRITICAL = "critical"
    HIGH = "high"
    WARNING = "warning"
    INFO = "info"
    DEBUG = "debug"


class AlertStatus(str, enum.Enum):
    """Alert status enumeration"""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    IGNORED = "ignored"


class Alert(TenantBase, Base):
    """Alert model"""
    __tablename__ = "alerts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source = Column(String(100), nullable=False, index=True)  # Engine that created the alert
    alert_type = Column(String(100), nullable=False, index=True)
    
    # Priority and status
    priority = Column(Enum(AlertPriority), default=AlertPriority.INFO)
    status = Column(Enum(AlertStatus), default=AlertStatus.OPEN)
    
    # Alert details
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    extra_metadata = Column(Text, nullable=True)  # JSON string
    
    # Resolution
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String(100), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    
    # Escalation
    escalated_at = Column(DateTime, nullable=True)
    escalated_to = Column(String(100), nullable=True)
    escalation_level = Column(Integer, default=0)
    
    # Notifications
    notification_count = Column(Integer, default=0)
    last_notification_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    notifications = relationship("Notification", back_populates="alert")
    
    def __repr__(self):
        return f"<Alert {self.id} - {self.priority} - {self.status}>"
