"""
Digest models
"""

from sqlalchemy import Column, String, Integer, DateTime, Boolean, Enum, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base
from app.models.tenant_base import TenantBase


class DigestSchedule(str, enum.Enum):
    """Digest schedule enumeration"""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    CUSTOM = "custom"


class Digest(TenantBase, Base):
    """Digest model"""
    __tablename__ = "digests"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Digest details
    name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)
    
    # Schedule
    schedule = Column(Enum(DigestSchedule), default=DigestSchedule.DAILY)
    schedule_config = Column(JSON, nullable=True)  # Custom schedule configuration
    
    # Recipients
    recipients = Column(JSON, nullable=False)  # List of recipients
    channels = Column(JSON, nullable=False)  # Channels to use
    
    # Filtering
    priority_filter = Column(JSON, nullable=True)  # Priority levels to include
    source_filter = Column(JSON, nullable=True)  # Sources to include
    
    # Status
    is_active = Column(Boolean, default=True)
    last_sent_at = Column(DateTime, nullable=True)
    next_send_at = Column(DateTime, nullable=True)
    
    # Content
    pending_notifications = Column(JSON, nullable=True)  # Queued notifications
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Digest {self.name} - {self.schedule}>"
