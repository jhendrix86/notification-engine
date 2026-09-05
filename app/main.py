"""
Notification Engine - Main Application
Centralized alert and notification system for the Autonomous Company OS
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from loguru import logger
from datetime import datetime
import os

from app.config import settings
from app.database import init_db
from app.routers import alerts, notifications, templates, channels, digests
from app.middleware.tenant import TenantMiddleware
from empire_operators.middleware import SafetyBoundaryMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting Notification Engine...")
    
    # Initialize database
    await init_db()
    
    logger.info("Notification Engine started successfully")
    yield
    
    logger.info("Shutting down Notification Engine...")


# Create FastAPI application
app = FastAPI(
    title="Notification Engine",
    description="Centralized alert and notification system for the Autonomous Company OS",
    version="1.0.0",
    lifespan=lifespan,
    # SECURITY_REVIEW.md finding: /docs, /redoc, /openapi.json were reachable
    # unauthenticated on every engine (dynamic-pentest-confirmed) - a full
    # interactive API browser plus every unauth write path. Disabled unless
    # DEBUG=true.
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
)

# Configure CORS — see SECURITY_REVIEW.md finding #1: no wildcard with
# credentials; allowed origins come from the ALLOWED_ORIGINS env var.
def _cors_allowed_origins() -> list:
    # SECURITY_REVIEW.md #1 — no wildcard with credentials. Set
    # ALLOWED_ORIGINS (comma-separated) when a browser client exists.
    import os
    return [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()]


app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add tenant middleware for multi-tenancy support
app.add_middleware(TenantMiddleware)

# Reject request bodies matching known-unsafe patterns (prompt injection,
# `drop table`, `<script>`) before they reach a router. empire_os
# SafetyBoundaryOperator — Phase B stretch wire, see
# empire_os/EMPIRE_OS_INTEGRATION_ANALYSIS.md + SECURITY_REVIEW.md.
app.add_middleware(SafetyBoundaryMiddleware)

# Include routers
app.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
app.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
app.include_router(templates.router, prefix="/templates", tags=["templates"])
app.include_router(channels.router, prefix="/channels", tags=["channels"])
app.include_router(digests.router, prefix="/digests", tags=["digests"])


@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "Notification Engine",
        "version": "1.0.0",
        "status": "operational",
        "description": "Centralized alert and notification system",
        "channels": ["email", "sms", "slack", "discord", "webhook"],
        "endpoints": {
            "alerts": "/alerts",
            "notifications": "/notifications",
            "templates": "/templates",
            "channels": "/channels",
            "digests": "/digests"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    logger.info("Health check performed")
    return {
        "status": "healthy",
        "service": "notification-engine",
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8037,
        reload=True
    )
