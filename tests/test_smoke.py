"""
Notification Engine smoke tests
"""
import pytest


@pytest.mark.asyncio
async def test_digest_import():
    """Verify digest models import without error"""
    from app.models.digest import Digest, DigestSchedule
    assert Digest is not None
    assert DigestSchedule.DAILY == "daily"
    assert DigestSchedule.HOURLY == "hourly"


@pytest.mark.asyncio
async def test_app_instantiation():
    """Verify FastAPI app instantiates without error"""
    from app.main import app
    assert app is not None
    assert app.title == "Notification Engine"
