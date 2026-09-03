"""
Channel models
"""

from sqlalchemy import Column, String, Integer, DateTime, Boolean, Enum, Text, JSON, Uuid
from datetime import datetime
import uuid
import enum

from app.database import Base
from app.models.tenant_base import TenantBase


class ChannelStatus(str, enum.Enum):
    """Channel status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEGRADED = "degraded"
    ERROR = "error"


class Channel(TenantBase, Base):
    """Channel configuration model"""
    __tablename__ = "channels"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Channel details
    channel_type = Column(String(50), nullable=False, unique=True)  # email, sms, slack, discord, webhook
    name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)
    
    # Configuration
    config = Column(JSON, nullable=False)  # Channel-specific configuration
    credentials = Column(JSON, nullable=True)  # Encrypted credentials
    
    # Status
    status = Column(Enum(ChannelStatus), default=ChannelStatus.ACTIVE)
    
    # Rate limiting
    rate_limit_per_minute = Column(Integer, default=100)
    rate_limit_per_hour = Column(Integer, default=1000)
    
    # Health
    last_health_check = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
    error_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Channel {self.channel_type} - {self.status}>"
