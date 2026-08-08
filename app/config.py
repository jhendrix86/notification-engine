"""
Configuration management for Notification Engine
"""

from pydantic_settings import BaseSettings
from typing import Optional, List
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # Database
    database_url: str = os.getenv("DATABASE_URL", "postgresql://localhost/notifications")
    
    # Redis
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Email (SendGrid)
    sendgrid_api_key: str = os.getenv("SENDGRID_API_KEY", "")
    default_email_from: str = os.getenv("DEFAULT_EMAIL_FROM", "notifications@company.com")
    
    # SMS (Twilio)
    twilio_account_sid: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    twilio_auth_token: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    twilio_phone_number: str = os.getenv("TWILIO_PHONE_NUMBER", "")
    
    # Slack
    slack_webhook_url: str = os.getenv("SLACK_WEBHOOK_URL", "")
    slack_default_channel: str = os.getenv("SLACK_DEFAULT_CHANNEL", "#alerts")
    
    # Discord
    discord_webhook_url: str = os.getenv("DISCORD_WEBHOOK_URL", "")
    
    # Rate Limiting
    rate_limit_per_minute: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "10"))
    rate_limit_per_hour: int = int(os.getenv("RATE_LIMIT_PER_HOUR", "100"))
    
    # Escalation
    escalation_hours: int = int(os.getenv("ESCALATION_HOURS", "24"))
    
    # Digest
    digest_enabled: bool = os.getenv("DIGEST_ENABLED", "true").lower() == "true"
    digest_interval_hours: int = int(os.getenv("DIGEST_INTERVAL_HOURS", "6"))
    
    # Application
    app_name: str = "Notification Engine"
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Integration
    global_state_manager_url: str = os.getenv("GLOBAL_STATE_MANAGER_URL", "http://localhost:8035")
    governance_engine_url: str = os.getenv("GOVERNANCE_ENGINE_URL", "http://localhost:8033")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # tolerate env vars owned by other libs (e.g. unkey-auth's UNKEY_*)


settings = Settings()
