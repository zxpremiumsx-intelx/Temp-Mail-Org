"""
Handler for /start command
Registers new users and displays welcome message
"""

import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

from db import get_session
from models import User

logger = logging.getLogger(__name__)

WELCOME_MESSAGE = """
🌟 *Welcome to Temp Mail Bot!* 🌟

Generate temporary email addresses instantly. Perfect for:
• Signing up for services without spam
• Protecting your real email
• One-time verifications

📋 *Available Commands:*

/newmail - Generate a new temporary email
/history - View your last 100 emails
/deletemail - Delete an email address
/start - Show this help message

━━━━━━━━━━━━━━━━━━━━━━
💡 *Tips:*
• You can have up to 100 active emails
• Oldest emails are auto-deleted when limit is reached
• Emails are unique and instantly active

Start by using /newmail to create your first email!
"""


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /start command.
    Registers user if new, then displays welcome message.
    """
    user = update.effective_user
    telegram_id = user.id
    username = user.username
    
    logger.info(f"Start command from user: {telegram_id} (@{username})")
    
    try:
        with get_session() as session:
            # Check if user exists
            existing_user = session.query(User).filter(
                User.telegram_id == telegram_id
            ).first()
            
            if existing_user:
                # Update username if changed
                if existing_user.username != username:
                    existing_user.username = username
                    logger.info(f"Updated username for {telegram_id}: {username}")
            else:
                # Create new user
                new_user = User(
                    telegram_id=telegram_id,
                    username=username,
                    created_at=datetime.utcnow()
                )
                session.add(new_user)
                logger.info(f"Registered new user: {telegram_id} (@{username})")
        
        # Send welcome message
        await update.message.reply_text(
            WELCOME_MESSAGE,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in start handler: {e}")
        await update.message.reply_text(
            "❌ An error occurred. Please try again later."
        )

