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
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
