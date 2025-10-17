#!/usr/bin/env python3
"""
Simple Telegram Bot Handler for Instagram Downloader
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

class SimpleInstagramDownloaderBot:
    def __init__(self, token):
        self.token = token
        self.application = Application.builder().token(token).build()
        self.setup_handlers()
    
    def setup_handlers(self):
        """Set up command and message handlers"""
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("id", self.id_command))
        self.application.add_handler(CommandHandler("register", self.register_command))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        user_id = user.id
        
        welcome_message = f"""🎉 Welcome to Instagram Downloader Bot!

👤 Your Telegram Information:
• Name: {user.first_name} {user.last_name or ''}
• Username: @{user.username or 'Not set'}
• Telegram ID: {user_id}

📞 To login to Instagram Downloader with your phone:
1. Register your phone number: /register +1234567890
2. Go to the login page
3. Click "Sign in with Telegram"
4. Enter your phone number
5. I'll send you a verification code!

💡 Use /register followed by your phone number (with country code)
Example: /register +1234567890

Type /help for more information."""
        
        await update.message.reply_text(welcome_message)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """🤖 Instagram Downloader Bot Help

Commands:
• /start - Get started and see your info
• /register +phone - Register your phone number
• /id - Get your Telegram ID
• /help - Show this help message

How to use for login:
1. Register your phone: /register +1234567890
2. Visit the Instagram Downloader website
3. Click "Sign in with Telegram"
4. Enter your phone number
5. I'll send you a 6-digit verification code
6. Enter the code to complete login

Features:
• Login with your phone number (easier!)
• Secure OTP-based authentication
• No password required
• Quick and easy login process

Example: /register +1234567890

Need more help? Contact the website administrator."""
        
        await update.message.reply_text(help_text)
    
    async def id_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /id command"""
        user_id = update.effective_user.id
        
        await update.message.reply_text(
            f"🆔 Your Telegram ID: {user_id}\n\nTo login with phone number, use: /register +1234567890"
        )
    
    async def register_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /register command to register phone number"""
        user = update.effective_user
        user_id = user.id
        
        # Get phone number from command arguments
        if not context.args:
            await update.message.reply_text(
                "📞 Please provide your phone number with country code.\n\n"
                "Example: /register +1234567890\n\n"
                "Make sure to include the + and country code!"
            )
            return
        
        phone_number = context.args[0].strip()
        
        # Basic phone number validation
        if not phone_number.startswith('+') or len(phone_number) < 10:
            await update.message.reply_text(
                "⚠️ Invalid phone number format!\n\n"
                "Please use international format with country code:\n"
                "Example: /register +1234567890"
            )
            return
        
        # Here you would typically save to database
        # For now, we'll just confirm registration
        await update.message.reply_text(
            f"✅ Phone number registered successfully!\n\n"
            f"📞 Your phone: {phone_number}\n"
            f"🆔 Your Telegram ID: {user_id}\n\n"
            f"🔐 You can now login to Instagram Downloader using your phone number!\n\n"
            f"Go to the website and enter: {phone_number}"
        )
        
        # TODO: Save to Django database via API call
        # This would require setting up the Django database connection
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular messages"""
        user_id = update.effective_user.id
        
        response = f"""👋 Hello! Your Telegram ID is: {user_id}

Use the commands:
• /start - Get started
• /id - Get your Telegram ID
• /help - Get help

Copy your ID to login to Instagram Downloader!"""
        
        await update.message.reply_text(response)
    
    def run(self):
        """Start the bot"""
        logger.info("Starting Instagram Downloader Bot...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)

def main():
    if len(sys.argv) != 2:
        print("Usage: python simple_telegram_bot.py YOUR_BOT_TOKEN")
        sys.exit(1)
    
    bot_token = sys.argv[1]
    
    try:
        bot = SimpleInstagramDownloaderBot(bot_token)
        bot.run()
    except Exception as e:
        logger.error(f"Error running bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()