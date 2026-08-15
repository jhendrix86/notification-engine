"""
channels.py is now real: /test attempts a genuine delivery through
app/services/delivery (honest failure when unconfigured), and
/status + /configure read/write the channels table for real.
"""

import httpx
import respx


async def test_status_with_nothing_configured_is_honestly_empty(client):
    r = await client.get("/channels/status")
    assert r.status_code == 200
    assert r.json() == {"total": 0, "channels": []}


async def test_test_channel_rejects_unknown_channel_type(client):
    r = await client.post("/channels/test", json={"channel_type": "carrier_pigeon"})
    assert r.status_code == 400


async def test_test_channel_reports_honest_failure_when_unconfigured(client):
    r = await client.post("/channels/test", json={"channel_type": "email", "recipient": "a@example.com"})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "failed"
    assert "not configured" in body["error"]


async def test_test_channel_persists_error_state_to_the_channel_row(client):
    await client.post("/channels/test", json={"channel_type": "email", "recipient": "a@example.com"})

    status = await client.get("/channels/status")
    channels = status.json()["channels"]
    assert len(channels) == 1
    assert channels[0]["channel_type"] == "email"
    assert channels[0]["status"] == "error"
    assert channels[0]["error_count"] == 1


@respx.mock
async def test_test_channel_succeeds_for_real_when_configured(client, monkeypatch):
    monkeypatch.setenv("SENDGRID_API_KEY", "test_key")
    import app.config as config_module
    monkeypatch.setattr(config_module.settings, "sendgrid_api_key", "test_key")
    respx.post("https://api.sendgrid.com/v3/mail/send").mock(return_value=httpx.Response(202))

    r = await client.post("/channels/test", json={"channel_type": "email", "recipient": "a@example.com"})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "success"

    status = await client.get("/channels/status")
    assert status.json()["channels"][0]["status"] == "active"


async def test_configure_channel_persists_real_config(client):
    r = await client.post("/channels/configure", json={
        "channel_type": "slack", "config": {"default_channel": "#alerts"},
    })
    assert r.status_code == 200
    body = r.json()
    assert body["channel_type"] == "slack"
    assert body["config"] == {"default_channel": "#alerts"}
    assert body["status"] == "active"


async def test_configure_channel_rejects_unknown_channel_type(client):
    r = await client.post("/channels/configure", json={"channel_type": "carrier_pigeon", "config": {}})
    assert r.status_code == 400


async def test_configure_then_test_reuses_the_same_channel_row(client):
    await client.post("/channels/configure", json={"channel_type": "discord", "config": {}})
    await client.post("/channels/test", json={"channel_type": "discord"})

    status = await client.get("/channels/status")
    assert status.json()["total"] == 1  # not two separate rows
