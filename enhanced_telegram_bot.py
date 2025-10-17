#!/usr/bin/env python3
"""
Enhanced Telegram Bot with Django Integration
"""

import os
import sys
import django
import asyncio
import logging

# Add the project directory to the Python path
project_dir = '/home/salohiddin/downlaoderf/instagram-downloader'
sys.path.append(project_dir)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'instagram_project.settings')
django.setup()

from django.contrib.auth.models import User
from downloader.models import TelegramUser
from telegram import Update, Bot, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class EnhancedInstagramDownloaderBot:
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
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(MessageHandler(filters.CONTACT, self.contact_handler))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        user_id = user.id
        
        # Check if user is already registered
        telegram_user = TelegramUser.objects.filter(telegram_id=user_id).first()
        
        if telegram_user and telegram_user.phone_number:
            # User is already registered
            welcome_message = f"""🎉 Welcome back to Instagram Downloader Bot!

✅ You are already registered!
📞 Your phone: {telegram_user.phone_number}
🔐 You can login to the website using your phone number.

Use /status to see your registration details."""
            
            await update.message.reply_text(welcome_message)
        else:
            # User needs to register
            welcome_message = f"""🎉 Welcome to Instagram Downloader Bot!

👤 Hello {user.first_name}!

📞 To use Instagram Downloader, please share your phone number by clicking the button below:

🔒 Your phone number will be used for secure login with OTP verification."""
            
            # Create share contact button
            contact_button = KeyboardButton(
                text="📞 Share My Phone Number",
                request_contact=True
            )
            
            keyboard = ReplyKeyboardMarkup(
                [[contact_button]],
                resize_keyboard=True,
                one_time_keyboard=True
            )
            
            await update.message.reply_text(
                welcome_message,
                reply_markup=keyboard
            )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """🤖 Instagram Downloader Bot Help

Commands:
• /start - Get started and register
• /status - Check your registration status
• /help - Show this help message

How to get started:
1️⃣ Send /start command
2️⃣ Click "Share My Phone Number" button
3️⃣ Done! You're registered!

How to login to website:
1️⃣ Visit Instagram Downloader website
2️⃣ Click "Sign in with Telegram"
3️⃣ Enter your phone number
4️⃣ Get OTP code in Telegram
5️⃣ Enter code and you're in!

Features:
• 🔘 One-click registration with phone sharing
• 🔒 Secure OTP-based authentication
• 🚀 No passwords needed
• ⚡ Super fast and easy!

Need more help? Contact the website administrator."""
        
        await update.message.reply_text(help_text)
    
    async def id_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /id command"""
        user_id = update.effective_user.id
        
        await update.message.reply_text(
            f"🆔 Your Telegram ID: {user_id}\n\nTo login with phone number, use: /register +1234567890"
        )
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command to check registration status"""
        user_id = update.effective_user.id
        
        try:
            telegram_user = TelegramUser.objects.filter(telegram_id=user_id).first()
            
            if telegram_user and telegram_user.phone_number:
                await update.message.reply_text(
                    f"✅ You are registered!\n\n"
                    f"📞 Phone: {telegram_user.phone_number}\n"
                    f"👤 Name: {telegram_user.first_name} {telegram_user.last_name or ''}\n\n"
                    f"🔐 You can login to Instagram Downloader using your phone number!"
                )
            else:
                await update.message.reply_text(
                    f"❌ You are not registered yet.\n\n"
                    f"Please register your phone number:\n"
                    f"/register +1234567890"
                )
        except Exception as e:
            logger.error(f"Error checking status for user {user_id}: {e}")
            await update.message.reply_text(
                "❌ Error checking your status. Please try again."
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
        
        # Register user in database
        try:
            # Check if user already exists
            telegram_user = TelegramUser.objects.filter(telegram_id=user_id).first()
            
            if telegram_user:
                # Update existing user
                telegram_user.phone_number = phone_number
                if user.first_name:
                    telegram_user.first_name = user.first_name
                if user.last_name:
                    telegram_user.last_name = user.last_name
                if user.username:
                    telegram_user.username = user.username
                telegram_user.save()
                
                # Update Django user
                django_user = telegram_user.user
                if user.first_name:
                    django_user.first_name = user.first_name
                if user.last_name:
                    django_user.last_name = user.last_name
                django_user.save()
                
                logger.info(f"Updated user {user_id} with phone {phone_number}")
                
                await update.message.reply_text(
                    f"🔄 Registration updated successfully!\n\n"
                    f"📞 Your phone: {phone_number}\n"
                    f"🆔 Your Telegram ID: {user_id}\n\n"
                    f"✅ You can now login to Instagram Downloader using your phone number!"
                )
            else:
                # Create new user
                # Create Django user
                django_username = f"user_{phone_number.replace('+', '').replace('-', '').replace(' ', '')}"
                counter = 1
                while User.objects.filter(username=django_username).exists():
                    django_username = f"user_{phone_number.replace('+', '').replace('-', '').replace(' ', '')}_{counter}"
                    counter += 1

                django_user = User.objects.create_user(
                    username=django_username,
                    first_name=user.first_name or phone_number,
                    last_name=user.last_name or '',
                    email=f"{django_username}@telegram.local"
                )

                # Create Telegram user
                telegram_user = TelegramUser.objects.create(
                    user=django_user,
                    telegram_id=user_id,
                    username=user.username or '',
                    first_name=user.first_name or '',
                    last_name=user.last_name or '',
                    phone_number=phone_number,
                    is_verified=True
                )
                
                logger.info(f"Created new user {user_id} with phone {phone_number}")
                
                await update.message.reply_text(
                    f"✅ Registration successful!\n\n"
                    f"📞 Your phone: {phone_number}\n"
                    f"🆔 Your Telegram ID: {user_id}\n"
                    f"👤 Name: {user.first_name or ''} {user.last_name or ''}\n\n"
                    f"🔐 You can now login to Instagram Downloader using your phone number!\n\n"
                    f"Go to the website and enter: {phone_number}"
                )
                
        except Exception as e:
            logger.error(f"Error registering user {user_id}: {e}")
            await update.message.reply_text(
                "❌ Registration failed. Please try again or contact support."
            )
    
    async def contact_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle shared contact (phone number)"""
        user = update.effective_user
        user_id = user.id
        contact = update.message.contact
        
        # Check if the shared contact is the user's own contact
        if contact.user_id != user_id:
            await update.message.reply_text(
                "⚠️ Please share your own phone number, not someone else's!",
                reply_markup=ReplyKeyboardMarkup(
                    [[KeyboardButton("📞 Share My Phone Number", request_contact=True)]],
                    resize_keyboard=True,
                    one_time_keyboard=True
                )
            )
            return
        
        phone_number = contact.phone_number
        
        # Add + if not present
        if not phone_number.startswith('+'):
            phone_number = '+' + phone_number
        
        try:
            # Check if user already exists
            telegram_user = TelegramUser.objects.filter(telegram_id=user_id).first()
            
            if telegram_user:
                # Update existing user
                telegram_user.phone_number = phone_number
                if user.first_name:
                    telegram_user.first_name = user.first_name
                if user.last_name:
                    telegram_user.last_name = user.last_name
                if user.username:
                    telegram_user.username = user.username
                telegram_user.save()
                
                # Update Django user
                django_user = telegram_user.user
                if user.first_name:
                    django_user.first_name = user.first_name
                if user.last_name:
                    django_user.last_name = user.last_name
                django_user.save()
                
                logger.info(f"Updated user {user_id} with phone {phone_number}")
                
                success_message = f"""✅ Registration Updated Successfully!

📞 Phone: {phone_number}
👤 Name: {user.first_name or ''} {user.last_name or ''}

🎉 You can now login to Instagram Downloader!
🔗 Visit the website and enter your phone number to get an OTP code."""
                
            else:
                # Create new user
                # Create Django user
                django_username = f"user_{phone_number.replace('+', '').replace('-', '').replace(' ', '')}"
                counter = 1
                while User.objects.filter(username=django_username).exists():
                    django_username = f"user_{phone_number.replace('+', '').replace('-', '').replace(' ', '')}_{counter}"
                    counter += 1

                django_user = User.objects.create_user(
                    username=django_username,
                    first_name=user.first_name or phone_number,
                    last_name=user.last_name or '',
                    email=f"{django_username}@telegram.local"
                )

                # Create Telegram user
                telegram_user = TelegramUser.objects.create(
                    user=django_user,
                    telegram_id=user_id,
                    username=user.username or '',
                    first_name=user.first_name or '',
                    last_name=user.last_name or '',
                    phone_number=phone_number,
                    is_verified=True
                )
                
                logger.info(f"Created new user {user_id} with phone {phone_number}")
                
                success_message = f"""✅ Registration Successful!

📞 Phone: {phone_number}
👤 Name: {user.first_name or ''} {user.last_name or ''}
🆔 Telegram ID: {user_id}

🎉 Welcome to Instagram Downloader!
🔗 Visit the website and enter your phone number to login with OTP."""
            
            # Remove keyboard and send success message
            await update.message.reply_text(
                success_message,
                reply_markup=ReplyKeyboardMarkup([["/status", "/help"]], resize_keyboard=True)
            )
                
        except Exception as e:
            logger.error(f"Error processing contact for user {user_id}: {e}")
            await update.message.reply_text(
                "❌ Registration failed. Please try again or contact support."
            )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular messages"""
        user_id = update.effective_user.id
        
        # Check if user is registered
        telegram_user = TelegramUser.objects.filter(telegram_id=user_id).first()
        
        if telegram_user and telegram_user.phone_number:
            response = f"""👋 Hello! You are already registered.

📞 Your phone: {telegram_user.phone_number}

🔗 Visit the website and login with your phone number!

Commands: /status /help"""
        else:
            response = f"""👋 Hello! To get started:

1️⃣ Send /start to register
2️⃣ Share your phone number
3️⃣ Login on the website!

Commands: /start /help"""
        
        await update.message.reply_text(response)
    
    def run(self):
        """Start the bot"""
        logger.info("Starting Enhanced Instagram Downloader Bot with Django integration...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)

def main():
    if len(sys.argv) != 2:
        print("Usage: python enhanced_telegram_bot.py YOUR_BOT_TOKEN")
        sys.exit(1)
    
    bot_token = sys.argv[1]
    
    try:
        bot = EnhancedInstagramDownloaderBot(bot_token)
        bot.run()
    except Exception as e:
        logger.error(f"Error running bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()