# SMS Provider Setup

This application supports two SMS providers: **Twilio** (preferred) and **Prelude** (fallback).

## Twilio Setup (Recommended)

Twilio is the preferred SMS provider as it doesn't require templates and has better pricing.

### 1. Get Twilio Credentials

1. Sign up for a [Twilio account](https://www.twilio.com/try-twilio)
2. Get your Account SID and Auth Token from the [Twilio Console](https://console.twilio.com/)
3. Purchase a phone number from the [Phone Numbers section](https://console.twilio.com/us1/develop/phone-numbers/manage/incoming)

### 2. Set Environment Variables

Add these to your `.env` file:

```bash
# Twilio Configuration (preferred)
TWILIO_ACCOUNT_SID=your_account_sid_here
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=+1234567890  # Required for sending SMS

# Prelude Configuration (fallback - optional)
PRELUDE_API_TOKEN=your_prelude_token_here
```

**Note**: The Twilio provider can be initialized with just `TWILIO_ACCOUNT_SID` and `TWILIO_AUTH_TOKEN`, but `TWILIO_PHONE_NUMBER` is required when actually sending SMS messages.

### 3. Features

- ✅ Direct message sending (no templates required)
- ✅ International phone number support
- ✅ Delivery status tracking
- ✅ Detailed error messages
- ✅ Cost tracking in metadata

## Prelude Setup (Fallback)

Prelude is used as a fallback if Twilio is not configured.

### 1. Get Prelude Credentials

1. Sign up for a [Prelude account](https://prelude.dev)
2. Get your API token from the dashboard

### 2. Set Environment Variables

```bash
PRELUDE_API_TOKEN=your_prelude_token_here
```

### 3. Features

- ✅ Template-based messaging (requires paid plan)
- ✅ Direct message sending (limited)
- ✅ International phone number support
- ✅ Detailed error messages

## Provider Selection

The application automatically selects the SMS provider based on available credentials:

1. **Twilio** - If `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, and `TWILIO_PHONE_NUMBER` are all set
2. **Prelude** - If Twilio is not configured but `PRELUDE_API_TOKEN` is set
3. **None** - If neither provider is configured

## Usage Examples

### Sending SMS via Service

```python
from app.notifications.service import notification_service

# Send a simple SMS
result = await notification_service.send_custom_sms(
    to="+1234567890",
    message="Hello from Sqipit!"
)

if result.success:
    print(f"SMS sent! Message ID: {result.message_id}")
else:
    print(f"SMS failed: {result.error}")
```

### Sending Queue Notifications

```python
# Send next-in-line notification
result = await notification_service.send_next_in_line_sms(
    customer_phone="+1234567890",
    customer_name="John Doe",
    queue_name="Coffee Shop",
    service_location="Downtown"
)
```

## Error Handling

Both providers return detailed error information:

```python
result = await notification_service.send_custom_sms(
    to="+1234567890",
    message="Test message"
)

if not result.success:
    print(f"Error: {result.error}")
    print(f"Error details: {result.metadata.get('error_details', {})}")
```

## Testing

To test SMS functionality without sending real messages, you can use Twilio's test credentials or set up a test environment with mock providers.

## Cost Considerations

- **Twilio**: Pay per message sent (~$0.0075 per SMS in the US)
- **Prelude**: Check their pricing for template-based messaging

## Troubleshooting

### Common Issues

1. **"SMS provider not configured"** - Set the required environment variables
2. **"Invalid phone number"** - Ensure phone numbers are in E.164 format (+1234567890)
3. **"Insufficient balance"** - Add funds to your Twilio account
4. **"Template not found"** - Prelude requires templates for most operations

### Debug Mode

Set `echo=True` in the database configuration to see detailed API responses.
