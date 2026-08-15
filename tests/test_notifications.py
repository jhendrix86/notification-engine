"""
notifications.py is now real: create/send/batch/retry/list all hit the
notifications table for real, and /send and /batch attempt real delivery
through app/services/delivery (mocked here via respx - conftest leaves
every provider unconfigured by default, so the "honest failure" tests
need no mocking at all).
"""

import httpx
import respx


async def test_send_without_sendgrid_configured_reports_honest_failure(client):
    # conftest leaves SENDGRID_API_KEY unset by default
    r = await client.post("/notifications/send", json={
        "recipient": "user@example.com", "channels": ["email"], "message": "hello",
    })
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "failed"
    assert "not configured" in body["error_message"]


async def test_send_requires_either_message_or_template(client):
    r = await client.post("/notifications/send", json={"recipient": "user@example.com", "channels": ["email"]})
    assert r.status_code == 400


async def test_send_requires_at_least_one_channel(client):
    r = await client.post("/notifications/send", json={"recipient": "a@b.com", "channels": [], "message": "hi"})
    assert r.status_code == 400


@respx.mock
async def test_send_email_persists_and_delivers_for_real(client, monkeypatch):
    monkeypatch.setenv("SENDGRID_API_KEY", "test_key")
    import app.config as config_module
    monkeypatch.setattr(config_module.settings, "sendgrid_api_key", "test_key")

    route = respx.post("https://api.sendgrid.com/v3/mail/send").mock(
        return_value=httpx.Response(202, headers={"X-Message-Id": "sg_msg_1"})
    )

    r = await client.post("/notifications/send", json={
        "recipient": "user@example.com", "channels": ["email"], "subject": "Hi", "message": "hello",
    })

    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "sent"
    assert body["external_id"] == "sg_msg_1"
    assert body["id"]  # a real generated UUID
    assert route.call_count == 1


@respx.mock
async def test_send_slack_delivers_for_real(client, monkeypatch):
    monkeypatch.setattr(
        __import__("app.config", fromlist=["settings"]).settings,
        "slack_webhook_url", "https://hooks.slack.com/services/test",
    )
    respx.post("https://hooks.slack.com/services/test").mock(return_value=httpx.Response(200, text="ok"))

    r = await client.post("/notifications/send", json={
        "recipient": "#alerts", "channels": ["slack"], "message": "something happened",
    })

    assert r.status_code == 200
    assert r.json()["status"] == "sent"


async def test_send_with_alert_id_links_and_increments_alert_notification_count(client):
    alert = (await client.post("/alerts/create", json={
        "source": "revenue-operations", "alert_type": "payment_failed", "title": "Payment Failed",
    })).json()

    r = await client.post("/notifications/send", json={
        "recipient": "user@example.com", "channels": ["email"], "message": "hi", "alert_id": alert["id"],
    })
    assert r.status_code == 200
    assert r.json()["alert_id"] == alert["id"]

    updated_alert = (await client.get(f"/alerts/{alert['id']}")).json()
    assert updated_alert["notification_count"] == 1


async def test_send_with_unknown_alert_id_is_a_real_404(client):
    r = await client.post("/notifications/send", json={
        "recipient": "user@example.com", "channels": ["email"], "message": "hi",
        "alert_id": "00000000-0000-0000-0000-000000000000",
    })
    assert r.status_code == 404


@respx.mock
async def test_send_with_template_renders_variables_for_real(client, monkeypatch):
    monkeypatch.setenv("SENDGRID_API_KEY", "test_key")
    import app.config as config_module
    monkeypatch.setattr(config_module.settings, "sendgrid_api_key", "test_key")
    respx.post("https://api.sendgrid.com/v3/mail/send").mock(return_value=httpx.Response(202))

    template = (await client.post("/templates/create", json={
        "name": "payment_failed", "body": "Your payment of {amount} failed", "channels": ["email"],
    })).json()

    r = await client.post("/notifications/send", json={
        "recipient": "user@example.com", "channels": ["email"],
        "template_id": template["id"], "data": {"amount": "$42"},
    })

    assert r.status_code == 200
    assert r.json()["message"] == "Your payment of $42 failed"

    updated_template = (await client.get(f"/templates/{template['id']}")).json()
    assert updated_template["usage_count"] == 1


async def test_send_with_unknown_template_is_a_real_404(client):
    r = await client.post("/notifications/send", json={
        "recipient": "user@example.com", "channels": ["email"],
        "template_id": "00000000-0000-0000-0000-000000000000",
    })
    assert r.status_code == 404


@respx.mock
async def test_batch_sends_to_every_recipient_for_real(client, monkeypatch):
    monkeypatch.setenv("SENDGRID_API_KEY", "test_key")
    import app.config as config_module
    monkeypatch.setattr(config_module.settings, "sendgrid_api_key", "test_key")
    route = respx.post("https://api.sendgrid.com/v3/mail/send").mock(return_value=httpx.Response(202))

    r = await client.post("/notifications/batch", json={
        "recipients": ["a@example.com", "b@example.com", "c@example.com"],
        "channels": ["email"], "message": "batch hello",
    })

    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 3
    assert body["sent"] == 3
    assert body["failed"] == 0
    assert route.call_count == 3


async def test_get_notification_returns_the_real_row(client):
    sent = (await client.post("/notifications/send", json={
        "recipient": "a@example.com", "channels": ["email"], "message": "hi",
    })).json()

    r = await client.get(f"/notifications/{sent['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == sent["id"]


async def test_get_unknown_notification_is_a_real_404(client):
    r = await client.get("/notifications/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404


async def test_list_notifications_filters_by_status_for_real(client):
    await client.post("/notifications/send", json={"recipient": "a@example.com", "channels": ["email"], "message": "hi"})

    r = await client.get("/notifications/", params={"status": "failed"})
    body = r.json()
    assert body["total"] == 1
    assert body["notifications"][0]["status"] == "failed"


@respx.mock
async def test_retry_notification_reattempts_real_delivery(client, monkeypatch):
    failed = (await client.post("/notifications/send", json={
        "recipient": "a@example.com", "channels": ["email"], "message": "hi",
    })).json()
    assert failed["status"] == "failed"

    monkeypatch.setenv("SENDGRID_API_KEY", "test_key")
    import app.config as config_module
    monkeypatch.setattr(config_module.settings, "sendgrid_api_key", "test_key")
    respx.post("https://api.sendgrid.com/v3/mail/send").mock(return_value=httpx.Response(202))

    r = await client.post(f"/notifications/{failed['id']}/retry")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "sent"
    assert body["retry_count"] == 1


async def test_retry_unknown_notification_is_a_real_404(client):
    r = await client.post("/notifications/00000000-0000-0000-0000-000000000000/retry")
    assert r.status_code == 404
