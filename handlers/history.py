"""
Handler for /history command
Shows user's email history
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from db import get_session
from models import Mail

logger = logging.getLogger(__name__)

# Maximum emails to show in history
MAX_HISTORY_DISPLAY = 100


async def history_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /history command.
    Displays the user's last 100 generated emails.
    """
    user = update.effective_user
    telegram_id = user.id
    
    logger.info(f"History command from user: {telegram_id}")
    
    try:
        with get_session() as session:
            # Fetch user's mails ordered by creation date (newest first)
            mails = session.query(Mail).filter(
                Mail.user_id == telegram_id
            ).order_by(Mail.created_at.desc()).limit(MAX_HISTORY_DISPLAY).all()
            
            if not mails:
                await update.message.reply_text(
                    "📭 *No emails found*\n\n"
                    "Use /newmail to create your first temporary email!",
                    parse_mode="Markdown"
                )
                return
            
            # Build history message
            message_parts = [f"📋 *Your Email History* ({len(mails)} emails)\n"]
            message_parts.append("━━━━━━━━━━━━━━━━━━━━━━\n")
            
            for idx, mail in enumerate(mails, 1):
                status = "🟢" if mail.is_active else "🔴"
                status_text = "Active" if mail.is_active else "Inactive"
                
                # Format date
                date_str = mail.created_at.strftime("%Y-%m-%d %H:%M")
                
                message_parts.append(
                    f"{idx}. {status} `{mail.email}`\n"
                    f"   _{status_text} • {date_str}_\n\n"
                )
            
            message_parts.append("━━━━━━━━━━━━━━━━━━━━━━\n")
            message_parts.append("💡 Use /deletemail to remove an email")
            
            full_message = "".join(message_parts)
            
            # Telegram message length limit is 4096 characters
            if len(full_message) > 4000:
                # Split into multiple messages
                await send_paginated_history(update, mails)
            else:
                await update.message.reply_text(
                    full_message,
                    parse_mode="Markdown"
                )
                
    except Exception as e:
        logger.error(f"Error in history handler: {e}")
        await update.message.reply_text(
            "❌ An error occurred. Please try again later."
        )


async def send_paginated_history(update: Update, mails: list) -> None:
    """
    Send history in multiple messages if too long.
    """
    page_size = 20
    total_pages = (len(mails) + page_size - 1) // page_size
    
    for page in range(total_pages):
        start_idx = page * page_size
        end_idx = min(start_idx + page_size, len(mails))
        page_mails = mails[start_idx:end_idx]
        
        message_parts = [f"📋 *Email History* (Page {page + 1}/{total_pages})\n"]
        message_parts.append("━━━━━━━━━━━━━━━━━━━━━━\n")
        
        for idx, mail in enumerate(page_mails, start_idx + 1):
            status = "🟢" if mail.is_active else "🔴"
            status_text = "Active" if mail.is_active else "Inactive"
            date_str = mail.created_at.strftime("%Y-%m-%d %H:%M")
            
            message_parts.append(
                f"{idx}. {status} `{mail.email}`\n"
                f"   _{status_text} • {date_str}_\n\n"
            )
        
        await update.message.reply_text(
            "".join(message_parts),
            parse_mode="Markdown"
        )

