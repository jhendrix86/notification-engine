"""
Notification models
"""

from sqlalchemy import Column, String, Integer, DateTime, Boolean, Enum, ForeignKey, Text, JSON, Uuid
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base
from app.models.tenant_base import TenantBase


class NotificationChannel(str, enum.Enum):
    """Notification channel enumeration"""
    EMAIL = "email"
    SMS = "sms"
    SLACK = "slack"
    DISCORD = "discord"
    WEBHOOK = "webhook"


class NotificationStatus(str, enum.Enum):
    """Notification status enumeration"""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


class Notification(TenantBase, Base):
    """Notification model"""
    __tablename__ = "notifications"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_id = Column(Uuid(as_uuid=True), ForeignKey("alerts.id"), nullable=True)
    template_id = Column(Uuid(as_uuid=True), ForeignKey("templates.id"), nullable=True)
    
    # Recipient
    recipient = Column(String(255), nullable=False, index=True)
    recipient_type = Column(String(50), default="email")  # email, phone, slack_user, etc.
    
    # Channels
    channels = Column(JSON, nullable=False)  # List of channels to use
    primary_channel = Column(Enum(NotificationChannel), nullable=False)
    
    # Content
    subject = Column(String(500), nullable=True)
    message = Column(Text, nullable=False)
    data = Column(JSON, nullable=True)  # Template variables
    
    # Status
    status = Column(Enum(NotificationStatus), default=NotificationStatus.PENDING)
    
    # Delivery
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    failed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # External IDs
    external_id = Column(String(255), nullable=True)  # SendGrid message ID, Twilio SID, etc.
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    alert = relationship("Alert", back_populates="notifications")
    template = relationship("Template")
    
    def __repr__(self):
        return f"<Notification {self.id} - {self.status} - {self.primary_channel}>"
