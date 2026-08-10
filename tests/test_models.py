"""
Real tests for the SQLAlchemy models - previously completely untested
despite being the only real (non-mock) part of this engine.
"""

from sqlalchemy import select

from app.models.alert import Alert, AlertPriority, AlertStatus
from app.models.notification import Notification, NotificationChannel, NotificationStatus
from app.models.template import Template
from app.models.channel import Channel, ChannelStatus
from app.models.digest import Digest, DigestSchedule


async def test_alert_notification_relationship_round_trips(db_session):
    alert = Alert(source="revenue-operations", alert_type="payment_failed", title="Payment Failed")
    db_session.add(alert)
    await db_session.flush()

    notification = Notification(
        alert_id=alert.id, recipient="ops@example.com", channels=["email"],
        primary_channel=NotificationChannel.EMAIL, message="Payment failed for pay_123",
    )
    db_session.add(notification)
    await db_session.commit()

    result = await db_session.execute(select(Alert).where(Alert.id == alert.id))
    fetched = result.scalar_one()
    await db_session.refresh(fetched, attribute_names=["notifications"])

    assert len(fetched.notifications) == 1
    assert fetched.notifications[0].recipient == "ops@example.com"


async def test_template_notification_relationship_round_trips(db_session):
    template = Template(name="payment_failed", body="Your payment of {{amount}} failed", channels=["email"])
    db_session.add(template)
    await db_session.flush()

    notification = Notification(
        template_id=template.id, recipient="a@example.com", channels=["email"],
        primary_channel=NotificationChannel.EMAIL, message="rendered message",
    )
    db_session.add(notification)
    await db_session.commit()

    result = await db_session.execute(select(Template).where(Template.id == template.id))
    fetched = result.scalar_one()
    await db_session.refresh(fetched, attribute_names=["notifications"])

    assert len(fetched.notifications) == 1
    assert fetched.notifications[0].template_id == template.id


async def test_notification_does_not_require_an_alert_or_template(db_session):
    """Both FKs are nullable - a standalone notification (not tied to any alert) must be valid."""
    notification = Notification(
        recipient="a@example.com", channels=["slack"],
        primary_channel=NotificationChannel.SLACK, message="standalone notification",
    )
    db_session.add(notification)
    await db_session.commit()
    await db_session.refresh(notification)

    assert notification.status == NotificationStatus.PENDING
    assert notification.alert_id is None


async def test_alert_defaults(db_session):
    alert = Alert(source="funnel-automation", alert_type="conversion_drop", title="Conversion drop")
    db_session.add(alert)
    await db_session.commit()
    await db_session.refresh(alert)

    assert alert.priority == AlertPriority.INFO
    assert alert.status == AlertStatus.OPEN
    assert alert.escalation_level == 0


async def test_channel_is_unique_by_type(db_session):
    from sqlalchemy.exc import IntegrityError

    db_session.add(Channel(channel_type="email", name="Email (SendGrid)", config={}))
    await db_session.commit()

    db_session.add(Channel(channel_type="email", name="Duplicate", config={}))
    try:
        await db_session.commit()
        assert False, "expected an IntegrityError for a duplicate channel_type"
    except IntegrityError:
        await db_session.rollback()


async def test_channel_defaults_to_active(db_session):
    channel = Channel(channel_type="slack", name="Slack", config={"webhook_url": "https://hooks.slack.com/x"})
    db_session.add(channel)
    await db_session.commit()
    await db_session.refresh(channel)

    assert channel.status == ChannelStatus.ACTIVE
    assert channel.error_count == 0


async def test_digest_persists_recipients_and_channels(db_session):
    digest = Digest(
        name="Daily Critical Alerts", schedule=DigestSchedule.DAILY,
        recipients=["admin@example.com"], channels=["email"],
    )
    db_session.add(digest)
    await db_session.commit()

    result = await db_session.execute(select(Digest).where(Digest.name == "Daily Critical Alerts"))
    fetched = result.scalar_one()
    assert fetched.recipients == ["admin@example.com"]
    assert fetched.is_active is True
