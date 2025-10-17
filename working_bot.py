#!/usr/bin/env python3
"""
Simple Working Telegram Bot for Instagram Downloader
"""

import os
import sys
import django
import logging
from telegram import Update, Bot, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from asgiref.sync import sync_to_async

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'instagram_project.settings')
django.setup()

# Import Django models after setup
from downloader.models import TelegramUser
from django.contrib.auth.models import User

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class SimpleWorkingBot:
    def __init__(self, token):
        self.token = token
        self.application = Application.builder().token(token).build()
        self.setup_handlers()
    
    def setup_handlers(self):
        """Set up command and message handlers"""
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(MessageHandler(filters.CONTACT, self.contact_handler))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        user_id = user.id
        
        # Check if user already exists in database
        try:
            telegram_user = await sync_to_async(TelegramUser.objects.get)(telegram_id=user_id)
            phone = telegram_user.phone_number or 'Not shared'
            await update.message.reply_text(
                f"🎉 Welcome back {user.first_name}!\n\n"
                f"✅ Your phone: {phone}\n"
                f"🔐 You can login to Instagram Downloader using your phone number.\n\n"
                f"🌐 Visit: http://127.0.0.1:8001/telegram-login/",
                reply_markup=ReplyKeyboardRemove()
            )
        except TelegramUser.DoesNotExist:
            # Show phone sharing button
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
                f"🎉 Welcome to Instagram Downloader Bot!\n\n"
                f"👤 Hello {user.first_name}!\n\n"
                f"📞 To use Instagram Downloader, please share your phone number by clicking the button below:\n\n"
                f"🔒 Your phone number will be used for secure login with OTP verification.",
                reply_markup=keyboard
            )
    
    async def contact_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle shared contact"""
        user = update.effective_user
        user_id = user.id
        contact = update.message.contact
        
        # Check if it's the user's own contact
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
        if not phone_number.startswith('+'):
            phone_number = '+' + phone_number
        
        # Create or update user in database
        try:
            # Try to get existing telegram user
            telegram_user = await sync_to_async(TelegramUser.objects.get)(telegram_id=user_id)
            telegram_user.phone_number = phone_number
            telegram_user.first_name = user.first_name
            telegram_user.last_name = user.last_name
            telegram_user.username = user.username
            telegram_user.is_verified = True
            await sync_to_async(telegram_user.save)()
        except TelegramUser.DoesNotExist:
            # Create new user
            username = f"user_{phone_number.replace('+', '').replace('-', '').replace(' ', '')}"
            
            # Ensure unique username
            base_username = username
            counter = 1
            while await sync_to_async(User.objects.filter(username=username).exists)():
                username = f"{base_username}_{counter}"
                counter += 1
            
            # Create Django user
            django_user = await sync_to_async(User.objects.create_user)(
                username=username,
                first_name=user.first_name or '',
                last_name=user.last_name or '',
                email=f"{username}@telegram.local"
            )
            
            # Create Telegram user profile
            telegram_user = await sync_to_async(TelegramUser.objects.create)(
                user=django_user,
                telegram_id=user_id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                phone_number=phone_number,
                is_verified=True
            )
        
        await update.message.reply_text(
            f"✅ Registration Successful!\n\n"
            f"📞 Phone: {phone_number}\n"
            f"👤 Name: {user.first_name} {user.last_name or ''}\n\n"
            f"🎉 You can now login to Instagram Downloader!\n"
            f"🌐 Visit: http://127.0.0.1:8001/telegram-login/\n"
            f"💡 Enter your phone number: {phone_number}",
            reply_markup=ReplyKeyboardRemove()
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        await update.message.reply_text(
            "🤖 Instagram Downloader Bot Help\n\n"
            "Commands:\n"
            "• /start - Get started and register\n"
            "• /help - Show this help\n\n"
            "How to use:\n"
            "1️⃣ Send /start\n"
            "2️⃣ Click 'Share My Phone Number'\n"
            "3️⃣ Go to website and login with your phone!\n\n"
            "🌐 Website: http://127.0.0.1:8001/telegram-login/"
        )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages"""
        user_id = update.effective_user.id
        
        try:
            telegram_user = await sync_to_async(TelegramUser.objects.get)(telegram_id=user_id)
            phone = telegram_user.phone_number or 'Not shared'
            await update.message.reply_text(
                f"👋 Hello! You're registered with phone: {phone}\n\n"
                f"🌐 Login at: http://127.0.0.1:8001/telegram-login/\n"
                f"📞 Use your phone: {phone}"
            )
        except TelegramUser.DoesNotExist:
            await update.message.reply_text(
                "👋 Hello! Send /start to register with your phone number!"
            )
    
    def run(self):
        """Start the bot"""
        print("🤖 Starting Simple Instagram Downloader Bot...")
        print("✅ Bot is ready to receive messages!")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)

def main():
    if len(sys.argv) != 2:
        print("Usage: python working_bot.py YOUR_BOT_TOKEN")
        print("\nExample:")
        print("python working_bot.py 8276877025:AAFFPx5w397Zris6iSzFCe4cs6yrcwnnx0E")
        sys.exit(1)
    
    bot_token = sys.argv[1]
    
    try:
        bot = SimpleWorkingBot(bot_token)
        bot.run()
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()