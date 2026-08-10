"""
Shared pytest fixtures: boots the real app against an isolated in-memory
SQLite database so every test exercises the real routers and real
SQLAlchemy models end to end.
"""

import os

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite://")

import pytest_asyncio
from asgi_lifespan import LifespanManager
from httpx import AsyncClient, ASGITransport
from sqlalchemy import event
from sqlalchemy.pool import StaticPool

import app.database as database_module

database_module.engine = database_module.create_async_engine(
    "sqlite+aiosqlite://",
    echo=False,
    poolclass=StaticPool,
    connect_args={"check_same_thread": False},
)
database_module.AsyncSessionLocal = database_module.async_sessionmaker(
    database_module.engine, class_=database_module.AsyncSession, expire_on_commit=False
)


@event.listens_for(database_module.engine.sync_engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    """SQLite ignores FK constraints unless this pragma is set per-connection."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


from app.main import app  # noqa: E402


@pytest_asyncio.fixture
async def db_engine():
    """A fresh database schema for each test - imports every model so all tables register."""
    from app.models import alert, notification, template, channel, digest  # noqa: F401

    async with database_module.engine.begin() as conn:
        await conn.run_sync(database_module.Base.metadata.drop_all)
        await conn.run_sync(database_module.Base.metadata.create_all)
    return database_module.engine


@pytest_asyncio.fixture
async def db_session(db_engine):
    """A real AsyncSession bound to the fresh schema, for model-layer tests."""
    async with database_module.AsyncSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_engine):
    """A live ASGI test client for router-layer tests."""
    async with LifespanManager(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            yield c
