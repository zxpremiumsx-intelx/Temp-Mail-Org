# Temp Mail Telegram Bot

A production-ready Telegram bot for generating temporary email addresses using Mailgun.

## Features

- 📧 Generate temporary email addresses instantly
- 📋 View history of last 100 emails
- 🗑️ Delete emails when no longer needed
- 🔄 Auto-delete oldest email when limit reached (100 emails per user)
- 🔒 Secure with environment variables

## Tech Stack

- **Python 3.11+**
- **python-telegram-bot v20+** (async)
- **PostgreSQL** with SQLAlchemy ORM
- **Mailgun API** for email management
- **Railway** compatible

## Project Structure

```
telegram-bot/
├── main.py              # Entry point
├── db.py                # Database configuration
├── models.py            # SQLAlchemy models
├── mailgun.py           # Mailgun API integration
├── handlers/
│   ├── __init__.py
│   ├── start.py         # /start command
│   ├── newmail.py       # /newmail command
│   ├── history.py       # /history command
│   └── deletemail.py    # /deletemail command
├── requirements.txt
├── .env.example
└── README.md
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | Yes | Bot token from @BotFather |
| `DATABASE_URL` | Yes | PostgreSQL connection URL |
| `MAILGUN_API_KEY` | Yes | Mailgun API key |
| `MAILGUN_DOMAIN` | Yes | Your Mailgun domain |
| `MAILGUN_WEBHOOK_URL` | No | Webhook for incoming mail |

## Local Development

### 1. Clone and Setup

```bash
cd telegram-bot
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your credentials
```

### 3. Run PostgreSQL (Docker)

```bash
docker run -d \
  --name temp-mail-db \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=tempmail \
  -p 5432:5432 \
  postgres:15
```

### 4. Start the Bot

```bash
python main.py
```

## Railway Deployment

### 1. Create Railway Project

1. Go to [railway.app](https://railway.app)
2. Create a new project
3. Add PostgreSQL plugin (Railway provides `DATABASE_URL` automatically)

### 2. Deploy from GitHub

1. Connect your GitHub repository
2. Railway will detect Python automatically

### 3. Configure Environment Variables

In Railway dashboard, add these variables:

```
TELEGRAM_BOT_TOKEN=your_bot_token
MAILGUN_API_KEY=your_mailgun_key
MAILGUN_DOMAIN=your_domain
```

Note: `DATABASE_URL` is automatically provided by Railway's PostgreSQL plugin.

### 4. Configure as Worker

In Railway settings:
- Set **Start Command**: `python main.py`
- Set **Type**: Worker (not Web)

Railway will auto-deploy on every push.

## Mailgun Setup

### 1. Create Mailgun Account

1. Sign up at [mailgun.com](https://mailgun.com)
2. Verify your domain or use sandbox domain

### 2. Get API Key

1. Go to **Settings** → **API Keys**
2. Copy your **Private API Key**

### 3. Domain Setup (for production)

1. Add and verify your domain in Mailgun
2. Configure MX records as instructed
3. Use your domain in `MAILGUN_DOMAIN`

### Sandbox Domain (for testing)

- Use the sandbox domain provided by Mailgun
- Limited to 5 authorized recipients
- Good for development only

## Database Schema

### Users Table

| Column | Type | Description |
|--------|------|-------------|
| telegram_id | BIGINT | Primary key (Telegram user ID) |
| username | VARCHAR(255) | Telegram username |
| created_at | TIMESTAMP | Registration date |

### Mails Table

| Column | Type | Description |
|--------|------|-------------|
| id | BIGINT | Primary key (auto-increment) |
| user_id | BIGINT | Foreign key to users |
| email | VARCHAR(255) | Generated email address |
| is_active | BOOLEAN | Whether email is active |
| created_at | TIMESTAMP | Creation date |

## Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Register and show welcome |
| `/newmail` | Generate new temp email |
| `/history` | Show last 100 emails |
| `/deletemail` | Delete an email |

## Error Handling

The bot handles errors gracefully:
- Database connection failures
- Mailgun API errors
- Invalid user input
- Session timeouts

All errors are logged with timestamps for debugging.

## Security Considerations

- ✅ No hardcoded secrets
- ✅ Environment variables for all credentials
- ✅ SQL injection protection via SQLAlchemy
- ✅ Input validation
- ✅ Rate limiting by Telegram

## License

MIT License - Feel free to use and modify.

## Support

For issues or questions, create a GitHub issue.

