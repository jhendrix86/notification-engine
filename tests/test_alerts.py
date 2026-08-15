"""alerts.py is now real: every endpoint reads/writes the alerts table."""


async def _create_alert(client, **overrides):
    payload = {"source": "revenue-operations", "alert_type": "payment_failed", "title": "Payment Failed"}
    payload.update(overrides)
    r = await client.post("/alerts/create", json=payload)
    assert r.status_code == 200
    return r.json()


async def test_create_alert_persists_a_real_row(client):
    body = await _create_alert(client, priority="critical", metadata={"payment_id": "pay_123"})
    assert body["title"] == "Payment Failed"
    assert body["status"] == "open"
    assert body["priority"] == "critical"
    assert body["metadata"] == {"payment_id": "pay_123"}
    assert body["id"]  # a real generated UUID, not "alert_123"


async def test_create_alert_requires_declared_fields(client):
    r = await client.post("/alerts/create", json={"source": "x"})
    assert r.status_code == 422


async def test_create_alert_rejects_invalid_priority(client):
    r = await client.post("/alerts/create", json={
        "source": "x", "alert_type": "y", "title": "z", "priority": "extremely bad",
    })
    assert r.status_code == 422


async def test_resolve_alert_updates_the_real_row(client):
    created = await _create_alert(client)
    r = await client.post(f"/alerts/{created['id']}/resolve", json={"resolved_by": "ops-bot", "resolution_notes": "Retried"})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "resolved"
    assert body["resolved_by"] == "ops-bot"


async def test_resolve_unknown_alert_is_a_real_404(client):
    r = await client.post("/alerts/00000000-0000-0000-0000-000000000000/resolve", json={"resolved_by": "ops-bot"})
    assert r.status_code == 404


async def test_escalate_alert_updates_the_real_row(client):
    created = await _create_alert(client)
    r = await client.post(f"/alerts/{created['id']}/escalate", json={"escalated_to": "oncall"})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "escalated"
    assert body["escalated_to"] == "oncall"
    assert body["escalation_level"] == 1


async def test_escalate_twice_increments_escalation_level(client):
    created = await _create_alert(client)
    await client.post(f"/alerts/{created['id']}/escalate", json={"escalated_to": "oncall"})
    r = await client.post(f"/alerts/{created['id']}/escalate", json={"escalated_to": "manager"})
    assert r.json()["escalation_level"] == 2


async def test_get_alert_returns_the_real_row(client):
    created = await _create_alert(client)
    r = await client.get(f"/alerts/{created['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == created["id"]


async def test_get_unknown_alert_is_a_real_404(client):
    r = await client.get("/alerts/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404


async def test_list_alerts_reflects_real_created_rows(client):
    await _create_alert(client, title="one")
    await _create_alert(client, title="two")

    r = await client.get("/alerts/")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 2
    assert {a["title"] for a in body["alerts"]} == {"one", "two"}


async def test_list_alerts_filters_by_priority_for_real(client):
    await _create_alert(client, priority="critical", title="crit-one")
    await _create_alert(client, priority="warning", title="warn-one")

    r = await client.get("/alerts/", params={"priority": "critical"})
    body = r.json()
    assert body["total"] == 1
    assert body["alerts"][0]["title"] == "crit-one"
