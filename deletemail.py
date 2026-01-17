"""
Handler for /deletemail command
Allows users to delete their temporary emails
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from db import get_session
from models import Mail
from mailgun import delete_email, MailgunError

logger = logging.getLogger(__name__)

# Conversation state
AWAITING_DELETE_SELECTION = 1


async def deletemail_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle /deletemail command.
    Shows list of emails and asks user to select one for deletion.
    """
    user = update.effective_user
    telegram_id = user.id
    
    logger.info(f"Deletemail command from user: {telegram_id}")
    
    try:
        with get_session() as session:
            # Fetch user's active mails
            mails = session.query(Mail).filter(
                Mail.user_id == telegram_id,
                Mail.is_active == True
            ).order_by(Mail.created_at.desc()).limit(100).all()
            
            if not mails:
                await update.message.reply_text(
                    "📭 *No emails to delete*\n\n"
                    "Use /newmail to create an email first!",
                    parse_mode="Markdown"
                )
                return ConversationHandler.END
            
            # Store mails in context for later reference
            context.user_data["delete_mails"] = [
                {"id": m.id, "email": m.email} for m in mails
            ]
            
            # Build selection message
            message_parts = ["🗑️ *Select Email to Delete*\n"]
            message_parts.append("━━━━━━━━━━━━━━━━━━━━━━\n\n")
            message_parts.append("Reply with the *number* or *email address*:\n\n")
            
            for idx, mail in enumerate(mails, 1):
                message_parts.append(f"{idx}. `{mail.email}`\n")
            
            message_parts.append("\n━━━━━━━━━━━━━━━━━━━━━━\n")
            message_parts.append("💡 Send /cancel to abort")
            
            await update.message.reply_text(
                "".join(message_parts),
                parse_mode="Markdown"
            )
            
            return AWAITING_DELETE_SELECTION
            
    except Exception as e:
        logger.error(f"Error in deletemail handler: {e}")
        await update.message.reply_text(
            "❌ An error occurred. Please try again later."
        )
        return ConversationHandler.END


async def delete_confirmation_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle user's selection for email deletion.
    Accepts either a number or email address.
    """
    user = update.effective_user
    telegram_id = user.id
    user_input = update.message.text.strip()
    
    logger.info(f"Delete selection from user {telegram_id}: {user_input}")
    
    # Get stored mails from context
    stored_mails = context.user_data.get("delete_mails", [])
    
    if not stored_mails:
        await update.message.reply_text(
            "❌ Session expired. Please use /deletemail again."
        )
        return ConversationHandler.END
    
    # Find the mail to delete
    mail_to_delete = None
    
    # Check if input is a number
    if user_input.isdigit():
        idx = int(user_input) - 1  # Convert to 0-indexed
        if 0 <= idx < len(stored_mails):
            mail_to_delete = stored_mails[idx]
    else:
        # Check if input matches an email
        user_input_lower = user_input.lower()
        for mail in stored_mails:
            if mail["email"].lower() == user_input_lower:
                mail_to_delete = mail
                break
    
    if not mail_to_delete:
        await update.message.reply_text(
            "❌ *Invalid selection*\n\n"
            "Please reply with a valid number or email address.\n"
            "Use /cancel to abort.",
            parse_mode="Markdown"
        )
        return AWAITING_DELETE_SELECTION
    
    # Perform deletion
    try:
        with get_session() as session:
            # Find mail in database
            db_mail = session.query(Mail).filter(
                Mail.id == mail_to_delete["id"],
                Mail.user_id == telegram_id
            ).first()
            
            if not db_mail:
                await update.message.reply_text(
                    "❌ Email not found or already deleted."
                )
                return ConversationHandler.END
            
            email_address = db_mail.email
            
            # Delete from Mailgun
            try:
                delete_email(email_address)
            except MailgunError as e:
                logger.warning(f"Mailgun deletion warning: {e}")
                # Continue with database deletion
            
            # Delete from database
            session.delete(db_mail)
            
            # Clear context
            context.user_data.pop("delete_mails", None)
            
            await update.message.reply_text(
                f"✅ *Email Deleted Successfully!*\n\n"
                f"🗑️ `{email_address}`\n\n"
                f"This email will no longer receive messages.",
                parse_mode="Markdown"
            )
            
            logger.info(f"Deleted email {email_address} for user {telegram_id}")
            
    except Exception as e:
        logger.error(f"Error deleting email: {e}")
        await update.message.reply_text(
            "❌ An error occurred during deletion. Please try again."
        )
    
    return ConversationHandler.END


async def cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle /cancel command to abort deletion.
    """
    # Clear stored mails
    context.user_data.pop("delete_mails", None)
    
    await update.message.reply_text(
        "❌ Deletion cancelled.",
        parse_mode="Markdown"
    )
    
    return ConversationHandler.END

