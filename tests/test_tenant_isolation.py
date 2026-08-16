"""
Verifies tenant isolation for notification-engine endpoints.
Tests that automatic query filtering actually isolates data between tenants.
"""

# Use fixed UUIDs that match what we create in conftest
TENANT_A = "3e2a7c54-a950-48f3-9eb9-d1eb6b2d1be2"
TENANT_B = "00000000-0000-0000-0000-000000000001"


async def _create_alert(client, tenant_id, name):
    resp = await client.post(
        "/alerts/",
        json={
            "name": name,
            "priority": "high",
            "source": "test-service",
            "message": "Test alert message"
        },
        headers={"X-Tenant-ID": tenant_id},
    )
    assert resp.status_code == 200
    return resp.json()["id"]


async def test_tenant_cannot_read_another_tenants_alert(client):
    alert_id = await _create_alert(client, TENANT_A, "Tenant A's Alert")

    same_tenant = await client.get(f"/alerts/{alert_id}", headers={"X-Tenant-ID": TENANT_A})
    assert same_tenant.status_code == 200

    other_tenant = await client.get(f"/alerts/{alert_id}", headers={"X-Tenant-ID": TENANT_B})
    assert other_tenant.status_code == 404


async def test_list_alerts_is_scoped_per_tenant(client):
    await _create_alert(client, TENANT_A, "A's Alert 1")
    await _create_alert(client, TENANT_A, "A's Alert 2")
    await _create_alert(client, TENANT_B, "B's Alert")

    a_listing = await client.get("/alerts/", headers={"X-Tenant-ID": TENANT_A})
    assert a_listing.status_code == 200
    assert a_listing.json()["total"] == 2

    b_listing = await client.get("/alerts/", headers={"X-Tenant-ID": TENANT_B})
    assert b_listing.status_code == 200
    assert b_listing.json()["total"] == 1


async def test_no_tenant_header_sees_everything(client):
    """Fail-open posture: no X-Tenant-ID means no filtering is applied."""
    await _create_alert(client, TENANT_A, "A's Alert")
    await _create_alert(client, TENANT_B, "B's Alert")

    unscoped = await client.get("/alerts/")
    assert unscoped.status_code == 200
    assert unscoped.json()["total"] == 2


async def test_tenant_cannot_modify_another_tenants_alert(client):
    alert_id = await _create_alert(client, TENANT_A, "Tenant A's Alert")

    # Try to resolve as tenant B
    resolve_response = await client.post(
        f"/alerts/{alert_id}/resolve",
        headers={"X-Tenant-ID": TENANT_B}
    )
    assert resolve_response.status_code == 404


async def test_notification_creation_respects_tenant_scoping(client):
    """Notification creation should be tenant-scoped."""
    alert_id = await _create_alert(client, TENANT_A, "Test Alert")

    # Create notification for tenant A
    notification_resp = await client.post(
        "/notifications/send",
        json={
            "alert_id": alert_id,
            "recipient": "test@example.com",
            "channel": "email",
            "subject": "Test notification",
            "message": "Test message body"
        },
        headers={"X-Tenant-ID": TENANT_A}
    )
    assert notification_resp.status_code == 200
    notification_id = notification_resp.json()["id"]

    # Tenant A can see the notification
    a_notification = await client.get(f"/notifications/{notification_id}", headers={"X-Tenant-ID": TENANT_A})
    assert a_notification.status_code == 200

    # Tenant B cannot see the notification
    b_notification = await client.get(f"/notifications/{notification_id}", headers={"X-Tenant-ID": TENANT_B})
    assert b_notification.status_code == 404


async def test_channel_configuration_respects_tenant_scoping(client):
    """Channel configurations should be tenant-scoped."""
    # Create channel for tenant A
    channel_resp = await client.post(
        "/channels/",
        json={
            "name": "Email Channel",
            "channel_type": "email",
            "config": {"from_address": "noreply@example.com"}
        },
        headers={"X-Tenant-ID": TENANT_A}
    )
    assert channel_resp.status_code == 200
    channel_id = channel_resp.json()["id"]

    # Tenant A can see the channel
    a_channel = await client.get(f"/channels/{channel_id}", headers={"X-Tenant-ID": TENANT_A})
    assert a_channel.status_code == 200

    # Tenant B cannot see the channel
    b_channel = await client.get(f"/channels/{channel_id}", headers={"X-Tenant-ID": TENANT_B})
    assert b_channel.status_code == 404


async def test_template_creation_respects_tenant_scoping(client):
    """Template creation should be tenant-scoped."""
    # Create template for tenant A
    template_resp = await client.post(
        "/templates/",
        json={
            "name": "Welcome Template",
            "subject": "Welcome {{name}}",
            "body": "Hello {{name}}, welcome!"
        },
        headers={"X-Tenant-ID": TENANT_A}
    )
    assert template_resp.status_code == 200
    template_id = template_resp.json()["id"]

    # Tenant A can see the template
    a_template = await client.get(f"/templates/{template_id}", headers={"X-Tenant-ID": TENANT_A})
    assert a_template.status_code == 200

    # Tenant B cannot see the template
    b_template = await client.get(f"/templates/{template_id}", headers={"X-Tenant-ID": TENANT_B})
    assert b_template.status_code == 404
