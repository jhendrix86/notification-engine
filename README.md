# Notification Engine

Centralized alert and notification system for the Autonomous Company OS. This engine handles all system alerts, notifications, and communication routing across all engines and channels.

## Features

- **Multi-Channel Support** - Email, SMS, Slack, Discord, webhooks
- **Alert Management** - Create, update, and manage alerts
- **Notification Routing** - Intelligent routing based on priority and type
- **Alert Prioritization** - Critical, warning, info, debug levels
- **Notification History** - Complete audit trail of all notifications
- **Template System** - Reusable notification templates
- **Rate Limiting** - Prevent notification spam
- **Escalation Rules** - Automatic escalation for unresolved alerts
- **Digest Mode** - Batch notifications for reduced noise
- **Integration Ready** - Connects with all other engines

## Architecture

```
┌─────────────┐    Events    ┌──────────────┐
│   All       │ ────────────> │  Notification │
│  Engines    │               │   Ingestion   │
└─────────────┘               └──────┬───────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
            ┌───────▼──────┐ ┌────▼────┐ ┌────▼──────┐
            │   Priority   │ │ Routing │ │ Templates  │
            │   Engine     │ │ Engine  │ │  Manager   │
            └──────────────┘ └─────────┘ └───────────┘
                    │                │
                    └────────────────┼────────────────┘
                                     │
                    ┌────────────────▼────────────────┐
                    │      Channel Dispatchers       │
                    │  (Email, SMS, Slack, Discord)  │
                    └─────────────────────────────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
            ┌───────▼──────┐ ┌────▼────┐ ┌────▼──────┐
            │   History    │ │ Rate    │ │ Escalation│
            │   Logger     │ │ Limiter │ │  Engine   │
            └──────────────┘ └─────────┘ └───────────┘
```

## Installation

### Prerequisites

- Python 3.9+
- Redis (for queuing and caching)
- PostgreSQL (for notification history)
- SendGrid (for email)
- Twilio (for SMS)
- Slack/Discord webhooks

### Local Development

```bash
# Clone repository
git clone https://github.com/autonomous-company/notification-engine.git
cd notification-engine

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your configuration

# Run the service
uvicorn app.main:app --reload --port 8037
```

### Docker Deployment

```bash
# Build and start all services
cd docker
docker-compose up -d

# View logs
docker-compose logs -f notification-engine

# Stop services
docker-compose down
```

## Configuration

Configuration is managed via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://localhost/notifications` | PostgreSQL connection URL |
| `REDIS_URL` | `redis://localhost:6379` | Redis connection URL |
| `SENDGRID_API_KEY` | - | SendGrid API key |
| `TWILIO_ACCOUNT_SID` | - | Twilio account SID |
| `TWILIO_AUTH_TOKEN` | - | Twilio auth token |
| `SLACK_WEBHOOK_URL` | - | Slack webhook URL |
| `DISCORD_WEBHOOK_URL` | - | Discord webhook URL |
| `DEFAULT_EMAIL_FROM` | `notifications@company.com` | Default sender email |
| `RATE_LIMIT_PER_MINUTE` | `10` | Max notifications per minute |
| `ESCALATION_HOURS` | `24` | Hours before escalation |

## API Endpoints

### Health & Info
- `GET /health` - Health check
- `GET /` - Service information

### Alert Management
- `POST /alerts/create` - Create alert
- `POST /alerts/{alert_id}/resolve` - Resolve alert
- `POST /alerts/{alert_id}/escalate` - Escalate alert
- `GET /alerts/{alert_id}` - Get alert details
- `GET /alerts` - List all alerts

### Notification Management
- `POST /notifications/send` - Send notification
- `POST /notifications/batch` - Send batch notifications
- `GET /notifications/{notification_id}` - Get notification details
- `GET /notifications` - List notifications
- `POST /notifications/{notification_id}/retry` - Retry failed notification

### Template Management
- `POST /templates/create` - Create template
- `GET /templates/{template_id}` - Get template
- `GET /templates` - List templates
- `PUT /templates/{template_id}` - Update template

### Channel Management
- `POST /channels/test` - Test channel
- `GET /channels/status` - Get channel status
- `POST /channels/configure` - Configure channel

### Digest Management
- `POST /digests/create` - Create digest schedule
- `GET /digests/{digest_id}` - Get digest details
- `POST /digests/{digest_id}/send` - Send digest immediately

## Usage Examples

### Send Notification

```python
import httpx

async def send_notification():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8037/notifications/send",
            json={
                "recipient": "user@example.com",
                "channels": ["email", "slack"],
                "priority": "critical",
                "subject": "System Alert",
                "message": "Payment processing failed",
                "data": {"payment_id": "pay_123"}
            }
        )
        return response.json()
```

### Create Alert

```python
async def create_alert():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8037/alerts/create",
            json={
                "source": "revenue-operations",
                "type": "payment_failed",
                "priority": "critical",
                "title": "Payment Processing Failed",
                "description": "Payment pay_123 failed to process",
                "metadata": {"payment_id": "pay_123", "amount": 97.0}
            }
        )
        return response.json()
```

### Create Template

```python
async def create_template():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8037/templates/create",
            json={
                "name": "payment_failed",
                "subject": "Payment Failed: {{payment_id}}",
                "body": "Payment {{payment_id}} for ${{amount}} failed. Please review.",
                "channels": ["email"],
                "variables": ["payment_id", "amount"]
            }
        )
        return response.json()
```

## Notification Channels

### Email
- SendGrid integration
- HTML and plain text support
- Template-based emails
- Attachment support
- Delivery tracking

### SMS
- Twilio integration
- Short code support
- Delivery receipts
- Rate limiting

### Slack
- Webhook integration
- Rich message formatting
- Thread support
- Channel routing

### Discord
- Webhook integration
- Embed support
- Role mentions
- Channel routing

### Webhooks
- Custom webhook endpoints
- Retry logic
- Signature verification
- Payload customization

## Alert Priorities

- **Critical** - Immediate attention required, all channels
- **High** - Urgent attention, email + Slack
- **Warning** - Attention needed, email only
- **Info** - Informational, digest mode
- **Debug** - Development only, log only

## Escalation Rules

1. **Critical alerts**: Escalate after 1 hour if unresolved
2. **High alerts**: Escalate after 4 hours if unresolved
3. **Warning alerts**: Escalate after 24 hours if unresolved
4. **Escalation channels**: Add SMS, notify additional recipients

## Rate Limiting

- Per recipient: 10 notifications per minute
- Per channel: 100 notifications per minute
- Burst allowance: 20 notifications in 10 seconds
- Digest mode: Unlimited (batched)

## Integration with Other Engines

### All Engines
- Emit alert events for critical issues
- Subscribe to notification preferences
- Update notification settings

### Global State Manager
- Store notification state
- Track alert resolution
- Audit notification history

### Governance Engine
- Approve critical notifications
- Validate notification content
- Ensure compliance

## Monitoring

### Health Check
```bash
curl http://localhost:8037/health
```

### Metrics
- Notifications sent per channel
- Alert resolution time
- Failed notification rate
- Channel latency
- Template usage

## Security

- API key authentication
- Webhook signature verification
- Rate limiting
- Input validation
- Audit logging

## Troubleshooting

### Email Not Sending
- Check SendGrid API key
- Verify recipient email
- Review rate limits
- Check template validity

### SMS Not Sending
- Check Twilio credentials
- Verify phone number format
- Review SMS rate limits
- Check delivery status

### Slack/Discord Not Sending
- Verify webhook URL
- Check rate limits
- Review message formatting
- Test webhook connectivity

## License

MIT License

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request
