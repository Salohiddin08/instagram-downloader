#!/usr/bin/env python3
"""
Telegram Bot Handler for Instagram Downloader

This bot helps users get their Telegram ID for authentication.
Run this separately from your Django app.

Usage:
python telegram_bot_handler.py YOUR_BOT_TOKEN
"""

import os
import sys
import asyncio
import logging
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class InstagramDownloaderBot:
    def __init__(self, token):
        self.token = token
        self.application = Application.builder().token(token).build()
        self.setup_handlers()
    
    def setup_handlers(self):
        """Set up command and message handlers"""
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("id", self.id_command))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        user_id = user.id
        
        welcome_message = f"""🎉 Welcome to Instagram Downloader Bot!

👤 *Your Telegram Information:*
• Name: {user.first_name} {user.last_name or ''}
• Username: @{user.username or 'Not set'}
• *Telegram ID:* `{user_id}`

🔐 *To login to Instagram Downloader:*
1\. Copy your Telegram ID: `{user_id}`
2\. Go to the login page
3\. Click "Sign in with Telegram"
4\. Paste your Telegram ID
5\. I'll send you a verification code!

Type /help for more information\."""
        
        await update.message.reply_text(
            welcome_message,
            parse_mode='MarkdownV2'
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """🤖 *Instagram Downloader Bot Help*

*Commands:*
• `/start` \- Get your Telegram ID for login
• `/id` \- Get your Telegram ID
• `/help` \- Show this help message

*How to use for login:*
1\. Get your Telegram ID with `/start` or `/id`
2\. Visit the Instagram Downloader website
3\. Click "Sign in with Telegram"
4\. Enter your Telegram ID
5\. I'll send you a 6\-digit verification code
6\. Enter the code to complete login

*Features:*
• Secure OTP\-based authentication
• No password required
• Quick and easy login process

Need more help? Contact the website administrator\."""
        
        await update.message.reply_text(
            help_text,
            parse_mode='MarkdownV2'
        )
    
    async def id_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /id command"""
        user_id = update.effective_user.id
        
        await update.message.reply_text(
            f"🆔 Your Telegram ID: `{user_id}`\n\nUse this ID to login to Instagram Downloader\!",
            parse_mode='MarkdownV2'
        )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular messages"""
        user_id = update.effective_user.id
        
        response = f"""👋 Hello\! Your Telegram ID is: `{user_id}`

Use the commands:
• `/start` \- Get started
• `/id` \- Get your Telegram ID
• `/help` \- Get help

Copy your ID to login to Instagram Downloader\!"""
        
        await update.message.reply_text(
            response,
            parse_mode='MarkdownV2'
        )
    
    def run(self):
        """Start the bot"""
        logger.info("Starting Instagram Downloader Bot...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)

def main():
    if len(sys.argv) != 2:
        print("Usage: python telegram_bot_handler.py YOUR_BOT_TOKEN")
        print("\nThis bot helps users get their Telegram ID for login.")
        print("Run this in a separate terminal from your Django app.")
        sys.exit(1)
    
    bot_token = sys.argv[1]
    
    try:
        bot = InstagramDownloaderBot(bot_token)
        bot.run()
    except Exception as e:
        logger.error(f"Error running bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()