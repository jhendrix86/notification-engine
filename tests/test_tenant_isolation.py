"""
Verifies tenant context assignment for notification-engine endpoints.
Tests that apply_tenant_context() correctly assigns tenant_id on create.
Note: Automatic query filtering is not yet implemented - this test validates
create-time tenant assignment only.
"""

from sqlalchemy import select

# Use fixed UUIDs that match what we create in conftest
TENANT_A = "3e2a7c54-a950-48f3-9eb9-d1eb6b2d1be2"
TENANT_B = "00000000-0000-0000-0000-000000000001"


async def test_apply_tenant_context_on_alert_create(client, db_session):
    """Verify that apply_tenant_context assigns tenant_id on alert creation."""
    from app.models.alert import Alert
    import uuid
    
    # Create alert for tenant A
    result = await client.post(
        "/alerts/",
        json={
            "name": "Test Alert",
            "priority": "high",
            "source": "test-service",
            "message": "Test alert message"
        },
        headers={"X-Tenant-ID": TENANT_A}
    )
    assert result.status_code == 200
    alert_id = result.json()["id"]
    
    # Verify tenant_id was correctly assigned
    alert = await db_session.get(Alert, uuid.UUID(alert_id))
    assert alert is not None
    assert str(alert.tenant_id) == TENANT_A


async def test_apply_tenant_context_on_notification_create(client, db_session):
    """Verify that apply_tenant_context assigns tenant_id on notification creation."""
    from app.models.notification import Notification
    import uuid
    
    # Create alert for tenant A
    alert_result = await client.post(
        "/alerts/",
        json={
            "name": "Test Alert",
            "priority": "high",
            "source": "test-service",
            "message": "Test alert message"
        },
        headers={"X-Tenant-ID": TENANT_A}
    )
    assert alert_result.status_code == 200
    alert_id = alert_result.json()["id"]
    
    # Create notification for tenant A
    notification_result = await client.post(
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
    assert notification_result.status_code == 200
    notification_id = notification_result.json()["id"]
    
    # Verify notification tenant_id was correctly assigned
    notification = await db_session.get(Notification, uuid.UUID(notification_id))
    assert notification is not None
    assert str(notification.tenant_id) == TENANT_A


async def test_apply_tenant_context_on_channel_create(client, db_session):
    """Verify that apply_tenant_context assigns tenant_id on channel creation."""
    from app.models.channel import Channel
    import uuid
    
    # Create channel for tenant A
    result = await client.post(
        "/channels/",
        json={
            "name": "Email Channel",
            "channel_type": "email",
            "config": {"from_address": "noreply@example.com"}
        },
        headers={"X-Tenant-ID": TENANT_A}
    )
    assert result.status_code == 200
    channel_id = result.json()["id"]
    
    # Verify channel tenant_id was correctly assigned
    channel = await db_session.get(Channel, uuid.UUID(channel_id))
    assert channel is not None
    assert str(channel.tenant_id) == TENANT_A


async def test_apply_tenant_context_on_template_create(client, db_session):
    """Verify that apply_tenant_context assigns tenant_id on template creation."""
    from app.models.template import Template
    import uuid
    
    # Create template for tenant A
    result = await client.post(
        "/templates/",
        json={
            "name": "Welcome Template",
            "subject": "Welcome {{name}}",
            "body": "Hello {{name}}, welcome!"
        },
        headers={"X-Tenant-ID": TENANT_A}
    )
    assert result.status_code == 200
    template_id = result.json()["id"]
    
    # Verify template tenant_id was correctly assigned
    template = await db_session.get(Template, uuid.UUID(template_id))
    assert template is not None
    assert str(template.tenant_id) == TENANT_A
