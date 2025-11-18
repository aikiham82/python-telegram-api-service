# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a REST API microservice that sends Telegram messages to phone numbers using Telethon (Telegram Client API). It allows sending messages to phone numbers without requiring them to be contacts.

## Key Dependencies

- **Flask**: REST API framework (port 5000 by default)
- **Telethon**: Telegram Client API library for async operations
- **python-dotenv**: Environment variable management
- **gunicorn**: Production WSGI server

## Development Setup

### Initial Authentication (First Time Only)

Before running the server for the first time, you must authenticate with Telegram:

```bash
python first_login.py
```

This creates a session file (`telegram_session.session` by default) that contains the authenticated session. This file is critical - the app cannot function without it.

### Running the Application

```bash
# Development mode
python app.py

# Production mode
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# Docker (recommended for production)
docker-compose up -d
```

### Installing Dependencies

```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Architecture

### Core Components

1. **app.py**: Main Flask application with REST endpoints
   - Global singleton `telegram_client` initialized on first use
   - Async/sync bridge pattern: Flask routes create event loops to call async Telethon functions
   - Three endpoints: `/health`, `/send-message`, `/send-batch`

2. **first_login.py**: One-time authentication script
   - Creates `.session` file with authenticated Telegram session
   - Handles 2FA if enabled on the account

### Async Pattern

The app uses a specific pattern to bridge Flask's synchronous world with Telethon's async API:

```python
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
result = loop.run_until_complete(send_telegram_message(...))
loop.close()
```

This pattern is used in both `/send-message` and `/send-batch` endpoints.

### Client Lifecycle

- `telegram_client` is a global singleton initialized on first API call via `get_telegram_client()`
- The client persists across requests (not recreated per request)
- Authorization check happens on client initialization - fails if `.session` file is missing or invalid

### Error Handling

The API uses structured error codes:
- `invalid_phone`: Phone number invalid or doesn't exist on Telegram
- `privacy_restricted`: User privacy settings block messages from non-contacts
- `send_failed`: Generic send error
- `missing_data`: Required fields missing in request
- `internal_error`: Server-side error

## Environment Variables

Required variables (must be set in `.env` file):
- `TELEGRAM_API_ID`: Telegram app ID from https://my.telegram.org/apps
- `TELEGRAM_API_HASH`: Telegram app hash from https://my.telegram.org/apps
- `TELEGRAM_PHONE_NUMBER`: Phone number for the Telegram account (international format)
- `SESSION_NAME`: Name of session file (default: `telegram_session`)
- `PORT`: Server port (default: 5000)

## Critical Files

- `.session` file: Contains authenticated Telegram session. **Must not be committed to git.** Service cannot run without this file.
- `.env`: Environment variables. **Must not be committed to git.**

## API Endpoints

### POST /send-message
Send single message to a phone number.

Request body:
```json
{
  "phone_number": "+5491112345678",
  "message": "Message text"
}
```

### POST /send-batch
Send multiple messages in one request. Processes messages sequentially (not in parallel).

Request body:
```json
{
  "messages": [
    {"phone_number": "+5491112345678", "message": "Message 1"},
    {"phone_number": "+5491187654321", "message": "Message 2"}
  ]
}
```

### GET /health
Health check endpoint.

## Common Issues

1. **"Cliente no autorizado" error**: Run `python first_login.py` to create session file
2. **FloodWaitError**: Telegram rate limiting - add delays between batch messages
3. **PhoneNumberInvalidError**: Number must be in international format with `+` prefix
4. **Privacy errors**: User has privacy settings that block messages from non-contacts

## Docker Deployment

The project includes Docker support with:
- `Dockerfile`: Multi-stage build with Python 3.11-slim base
- `docker-compose.yml`: Development and production setup
- `.dockerignore`: Optimized build context

**Critical**: The `.session` file must be generated on the host BEFORE building the Docker image (run `first_login.py` locally). The Docker container mounts this file as read-only.

See `DEPLOYMENT.md` for detailed deployment instructions for various hosting platforms (Render, Railway, Fly.io, DigitalOcean, VPS).

## Testing

No test suite is currently implemented. Manual testing should use the API endpoints with tools like curl, Postman, or n8n.
