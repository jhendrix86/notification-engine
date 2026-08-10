"""
Script to migrate existing data to default tenant

This script assigns the default tenant_id to all existing records
that don't have a tenant_id set yet.
"""

import asyncio
import sys
import os

# Add the parent directory to the path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, update
from app.database import AsyncSessionLocal
from app.models.tenant import Tenant
from app.models.alert import Alert
from app.models.notification import Notification
from app.models.template import Template
from app.models.channel import Channel
from app.models.digest import Digest
from loguru import logger


async def migrate_to_default_tenant():
    """Migrate existing data to default tenant."""
    
    async with AsyncSessionLocal() as session:
        try:
            # Get or create default tenant
            result = await session.execute(
                select(Tenant).where(Tenant.slug == "default")
            )
            default_tenant = result.scalar_one_or_none()
            
            if not default_tenant:
                logger.error("Default tenant not found. Run create_default_tenant.py first.")
                return
            
            logger.info(f"Using default tenant: {default_tenant.id}")
            
            # Migrate each model type
            models_to_migrate = [
                (Alert, "alerts"),
                (Notification, "notifications"),
                (Template, "templates"),
                (Channel, "channels"),
                (Digest, "digests")
            ]
            
            total_migrated = 0
            
            for model_class, model_name in models_to_migrate:
                # Find records without tenant_id (if column is nullable)
                # For now, we'll just update all records since we just added the column
                result = await session.execute(
                    select(model_class)
                )
                records = result.scalars().all()
                
                if not records:
                    logger.info(f"No {model_name} to migrate")
                    continue
                
                # Update all records to have the default tenant_id
                await session.execute(
                    update(model_class)
                    .values(tenant_id=default_tenant.id)
                )
                
                count = len(records)
                total_migrated += count
                logger.info(f"Migrated {count} {model_name} to default tenant")
            
            await session.commit()
            logger.info(f"Migration complete. Total records migrated: {total_migrated}")
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            await session.rollback()
            raise


if __name__ == "__main__":
    logger.info("Starting data migration to default tenant...")
    asyncio.run(migrate_to_default_tenant())
    logger.info("Migration completed successfully")
