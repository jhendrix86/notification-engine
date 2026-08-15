"""
digests.py is now real: create/get hit the digests table, and /send
compiles a real digest from actually-open Alert rows and dispatches it
for real through app/services/delivery.
"""

import httpx
import respx


async def _create_digest(client, **overrides):
    payload = {
        "name": "Daily Critical Alerts", "schedule": "daily",
        "recipients": ["admin@example.com"], "channels": ["email"],
    }
    payload.update(overrides)
    r = await client.post("/digests/create", json=payload)
    assert r.status_code == 200
    return r.json()


async def test_create_digest_persists_a_real_row(client):
    body = await _create_digest(client)
    assert body["name"] == "Daily Critical Alerts"
    assert body["is_active"] is True
    assert body["next_send_at"] is not None
    assert body["id"]  # a real generated UUID, not "digest_123"


async def test_get_digest_returns_the_real_row(client):
    created = await _create_digest(client)
    r = await client.get(f"/digests/{created['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == created["id"]


async def test_get_unknown_digest_is_a_real_404(client):
    r = await client.get("/digests/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404


async def test_send_digest_with_no_open_alerts_is_honest(client):
    digest = await _create_digest(client)

    r = await client.post(f"/digests/{digest['id']}/send")
    assert r.status_code == 200
    body = r.json()
    assert body["alerts_included"] == 0
    # No SendGrid config in this test - real honest failure, not a fabricated "sent".
    assert body["status"] == "failed"
    assert body["recipients_notified"] == 0


@respx.mock
async def test_send_digest_compiles_and_delivers_real_open_alerts(client, monkeypatch):
    monkeypatch.setenv("SENDGRID_API_KEY", "test_key")
    import app.config as config_module
    monkeypatch.setattr(config_module.settings, "sendgrid_api_key", "test_key")
    respx.post("https://api.sendgrid.com/v3/mail/send").mock(return_value=httpx.Response(202))

    await client.post("/alerts/create", json={
        "source": "revenue-operations", "alert_type": "payment_failed", "title": "Payment Failed", "priority": "critical",
    })
    await client.post("/alerts/create", json={
        "source": "funnel-automation", "alert_type": "conversion_drop", "title": "Conversion Drop", "priority": "warning",
    })

    digest = await _create_digest(client)
    r = await client.post(f"/digests/{digest['id']}/send")

    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "sent"
    assert body["alerts_included"] == 2
    assert body["recipients_notified"] == 1


@respx.mock
async def test_send_digest_respects_its_own_priority_filter(client, monkeypatch):
    monkeypatch.setenv("SENDGRID_API_KEY", "test_key")
    import app.config as config_module
    monkeypatch.setattr(config_module.settings, "sendgrid_api_key", "test_key")
    respx.post("https://api.sendgrid.com/v3/mail/send").mock(return_value=httpx.Response(202))

    await client.post("/alerts/create", json={
        "source": "revenue-operations", "alert_type": "payment_failed", "title": "Critical One", "priority": "critical",
    })
    await client.post("/alerts/create", json={
        "source": "funnel-automation", "alert_type": "conversion_drop", "title": "Just Info", "priority": "info",
    })

    digest = await _create_digest(client, priority_filter=["critical"])
    r = await client.post(f"/digests/{digest['id']}/send")

    assert r.json()["alerts_included"] == 1


async def test_send_digest_requires_at_least_one_channel(client):
    digest = await _create_digest(client, channels=[])
    r = await client.post(f"/digests/{digest['id']}/send")
    assert r.status_code == 400


async def test_send_unknown_digest_is_a_real_404(client):
    r = await client.post("/digests/00000000-0000-0000-0000-000000000000/send")
    assert r.status_code == 404
