"""templates.py is now real: every endpoint reads/writes the templates table."""


async def _create_template(client, **overrides):
    payload = {"name": "payment_failed", "body": "Your payment of {amount} failed", "channels": ["email"]}
    payload.update(overrides)
    r = await client.post("/templates/create", json=payload)
    assert r.status_code == 200
    return r.json()


async def test_create_template_persists_a_real_row(client):
    body = await _create_template(client)
    assert body["name"] == "payment_failed"
    assert body["is_active"] is True
    assert body["usage_count"] == 0
    assert body["id"]  # a real generated UUID, not "template_123"


async def test_create_template_requires_declared_fields(client):
    r = await client.post("/templates/create", json={"name": "x"})
    assert r.status_code == 422


async def test_create_template_rejects_duplicate_name(client):
    await _create_template(client)
    r = await client.post("/templates/create", json={
        "name": "payment_failed", "body": "different body", "channels": ["email"],
    })
    assert r.status_code == 409


async def test_get_template_returns_the_real_row(client):
    created = await _create_template(client)
    r = await client.get(f"/templates/{created['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == created["id"]


async def test_get_unknown_template_is_a_real_404(client):
    r = await client.get("/templates/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404


async def test_update_template_persists_changes(client):
    created = await _create_template(client)
    r = await client.put(f"/templates/{created['id']}", json={"is_active": False, "body": "new body"})
    assert r.status_code == 200
    body = r.json()
    assert body["is_active"] is False
    assert body["body"] == "new body"

    refetched = await client.get(f"/templates/{created['id']}")
    assert refetched.json()["is_active"] is False


async def test_list_templates_reflects_real_created_rows(client):
    await _create_template(client, name="one")
    await _create_template(client, name="two")

    r = await client.get("/templates/")
    body = r.json()
    assert body["total"] == 2
    assert {t["name"] for t in body["templates"]} == {"one", "two"}


async def test_list_templates_filters_by_is_active_for_real(client):
    created = await _create_template(client, name="active-one")
    await client.put(f"/templates/{created['id']}", json={"is_active": False})
    await _create_template(client, name="active-two")

    r = await client.get("/templates/", params={"is_active": True})
    body = r.json()
    assert body["total"] == 1
    assert body["templates"][0]["name"] == "active-two"
