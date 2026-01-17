"""
Telegram Bot for Temp Mail Service
Main entry point - Railway compatible
"""

import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

from db import init_db, get_session
from handlers.start import start_handler
from handlers.newmail import newmail_handler
from handlers.history import history_handler
from handlers.deletemail import deletemail_handler, delete_confirmation_handler, cancel_handler

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states for delete flow
AWAITING_DELETE_SELECTION = 1


def main() -> None:
    """Main function to start the bot."""
    
    # Get bot token from environment
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")
    
    # Initialize database
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized successfully")
    
    # Create application
    application = Application.builder().token(bot_token).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("newmail", newmail_handler))
    application.add_handler(CommandHandler("history", history_handler))
    
    # Add conversation handler for delete flow
    delete_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("deletemail", deletemail_handler)],
        states={
            AWAITING_DELETE_SELECTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, delete_confirmation_handler)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_handler)],
    )
    application.add_handler(delete_conv_handler)
    
    # Start the bot
    logger.info("Starting Telegram bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

