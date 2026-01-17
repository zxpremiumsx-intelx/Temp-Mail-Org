"""
Handler for /newmail command
Generates new temporary email addresses
"""

import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy import func

from db import get_session
from models import User, Mail
from mailgun import create_email, delete_email, MailgunError

logger = logging.getLogger(__name__)

# Maximum number of emails per user
MAX_MAILS_PER_USER = 100


async def newmail_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /newmail command.
    Generates a new temporary email address for the user.
    Automatically deletes oldest email if limit is exceeded.
    """
    user = update.effective_user
    telegram_id = user.id
    
    logger.info(f"Newmail command from user: {telegram_id}")
    
    # Send typing indicator
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing"
    )
    
    try:
        with get_session() as session:
            # Ensure user exists
            db_user = session.query(User).filter(
                User.telegram_id == telegram_id
            ).first()
            
            if not db_user:
                # Auto-register user
                db_user = User(
                    telegram_id=telegram_id,
                    username=user.username,
                    created_at=datetime.utcnow()
                )
                session.add(db_user)
                session.flush()
                logger.info(f"Auto-registered user: {telegram_id}")
            
            # Count current mails
            mail_count = session.query(func.count(Mail.id)).filter(
                Mail.user_id == telegram_id
            ).scalar()
            
            # Check if limit exceeded - delete oldest if needed
            if mail_count >= MAX_MAILS_PER_USER:
                await handle_mail_limit(session, telegram_id, update)
            
            # Generate new email via Mailgun
            try:
                email_address, route_id = create_email()
            except MailgunError as e:
                logger.error(f"Mailgun error: {e}")
                await update.message.reply_text(
                    "❌ Failed to generate email. Please try again later."
                )
                return
            
            # Save to database
            new_mail = Mail(
                user_id=telegram_id,
                email=email_address,
                is_active=True,
                created_at=datetime.utcnow()
            )
            session.add(new_mail)
            
            # Get updated count
            new_count = mail_count + 1 if mail_count < MAX_MAILS_PER_USER else mail_count
            
            # Send success message
            await update.message.reply_text(
                f"✅ *New Email Created!*\n\n"
                f"📧 `{email_address}`\n\n"
                f"_Tap to copy_\n\n"
                f"📊 You have {new_count}/{MAX_MAILS_PER_USER} emails",
                parse_mode="Markdown"
            )
            
            logger.info(f"Created email {email_address} for user {telegram_id}")
            
    except Exception as e:
        logger.error(f"Error in newmail handler: {e}")
        await update.message.reply_text(
            "❌ An error occurred. Please try again later."
        )


async def handle_mail_limit(session, telegram_id: int, update: Update) -> None:
    """
    Handle case when user has reached mail limit.
    Deletes the oldest email to make room for new one.
    """
    # Find oldest mail
    oldest_mail = session.query(Mail).filter(
        Mail.user_id == telegram_id
    ).order_by(Mail.created_at.asc()).first()
    
    if oldest_mail:
        old_email = oldest_mail.email
        
        # Delete from Mailgun
        try:
            delete_email(old_email)
        except MailgunError as e:
            logger.warning(f"Failed to delete from Mailgun: {e}")
            # Continue with database deletion anyway
        
        # Delete from database
        session.delete(oldest_mail)
        session.flush()
        
        logger.info(f"Auto-deleted oldest email {old_email} for user {telegram_id}")
        
        # Notify user
        await update.message.reply_text(
            f"⚠️ *Mail limit reached ({MAX_MAILS_PER_USER})*\n\n"
            f"Auto-deleted oldest email:\n"
            f"`{old_email}`",
            parse_mode="Markdown"
        )

