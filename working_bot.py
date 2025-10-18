#!/usr/bin/env python3
"""
Social Media Downloader Bot
Supports: Instagram, Facebook, TikTok, Pinterest
"""

import os
import sys
import django
import logging
import threading
from telegram import Update, Bot, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from asgiref.sync import sync_to_async

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'instagram_project.settings')
django.setup()

# Import Django models after setup
from downloader.models import TelegramUser, DownloadedVideo
from downloader.utils import detect_platform, validate_url, download_video
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
        self.application.add_handler(MessageHandler(filters.Entity("url") | filters.Regex(r'https?://'), self.handle_url))
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
                f"🔐 You can now download from Instagram, Facebook, TikTok, Pinterest!\n\n"
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
                f"🎉 Social Media Downloader Bot'ga xush kelibsiz!\n\n"
                f"👤 Salom {user.first_name}!\n\n"
                f"📱 Instagram, Facebook, TikTok, Pinterest'dan videolarni yuklab oling!\n\n"
                f"📞 Iltimos, quyidagi tugmani bosib telefon raqamingizni ulashing:\n\n"
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
            "🤖 Social Media Downloader Bot Yordam\n\n"
            "📱 Qo'llab quvvatlanadigan platformalar:\n"
            "• Instagram (postlar, reels, hikoyalar, rasmlar)\n"
            "• Facebook (videolar, watch, rasmlar)\n"
            "• TikTok (videolar, qisqa havolalar)\n"
            "• Pinterest (pinlar, videolar, rasmlar)\n\n"
            "Buyruqlar:\n"
            "• /start - Boshlash va ro'yxatdan o'tish\n"
            "• /help - Ushbu yordamni ko'rsatish\n\n"
            "Qanday foydalanish:\n"
            "1️⃣ /start buyrug'ini yuboring va ro'yxatdan o'ting\n"
            "2️⃣ Telefon raqamingizni ulashing\n"
            "3️⃣ Istalgan video havolasini yuboring\n"
            "4️⃣ Bot videoni yuklab oladi va yuboradi!\n\n"
            "🌐 Veb-sayt: http://127.0.0.1:8001/telegram-login/"
        )
    
    async def handle_url(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle video URLs for downloading"""
        user = update.effective_user
        user_id = user.id
        url = update.message.text.strip()
        
        # Check if user is registered
        try:
            telegram_user = await sync_to_async(TelegramUser.objects.get)(telegram_id=user_id)
        except TelegramUser.DoesNotExist:
            await update.message.reply_text(
                "⚠️ Please register first by sending /start"
            )
            return
        
        # Detect platform
        platform = detect_platform(url)
        
        if platform == 'other':
            await update.message.reply_text(
                "❌ Unsupported URL format!\n\n"
                "📱 Supported platforms:\n"
                "• Instagram\n"
                "• Facebook\n"
                "• TikTok\n"
                "• Pinterest\n\n"
                "Please send a valid video URL from one of these platforms."
            )
            return
        
        # Validate URL
        is_valid, message = validate_url(url, platform)
        if not is_valid:
            await update.message.reply_text(
                f"❌ {message}\n\n"
                "Please check your URL and try again."
            )
            return
        
        # Send processing message
        processing_msg = await update.message.reply_text(
            f"🚀 Processing {platform.title()} video...\n"
            f"🔗 URL: {url[:50]}{'...' if len(url) > 50 else ''}\n\n"
            "⏳ This may take a few moments..."
        )
        
        try:
            # Create download record
            video_obj = await sync_to_async(DownloadedVideo.objects.create)(
                user=telegram_user.user,
                url=url,
                platform=platform,
                title='Processing...',
                status='pending'
            )
            
            # Start download in background
            async def download_and_notify():
                try:
                    # Run the sync download function in a thread
                    result = await sync_to_async(download_video)(video_obj)
                    await self.send_download_result(update, processing_msg, result)
                except Exception as e:
                    await processing_msg.edit_text(
                        f"❌ Download failed: {str(e)}\n\n"
                        "Please try again or contact support."
                    )
            
            # Schedule the download task
            import asyncio
            asyncio.create_task(download_and_notify())
            
        except Exception as e:
            await processing_msg.edit_text(
                f"❌ Download failed: {str(e)}\n\n"
                "Please try again or contact support."
            )
    
    async def send_download_result(self, update: Update, processing_msg, video_obj):
        """Send download result to user"""
        try:
            if video_obj.status == 'completed' and video_obj.file_path and os.path.exists(video_obj.file_path):
                # Try to send media file (video or image)
                try:
                    with open(video_obj.file_path, 'rb') as media_file:
                        media_type = getattr(video_obj, 'media_type', 'video')
                        
                        if media_type == 'image':
                            await update.message.reply_photo(
                                photo=media_file,
                                caption=f"✅ {video_obj.platform.title()}dan rasm yuklab olindi!\n\n"
                                       f"🖼️ Sarlavha: {video_obj.title}\n"
                                       f"📅 Yuklangan: {video_obj.completed_at.strftime('%Y-%m-%d %H:%M')}"
                            )
                        else:
                            await update.message.reply_video(
                                video=media_file,
                                caption=f"✅ {video_obj.platform.title()}dan video yuklab olindi!\n\n"
                                       f"🎥 Sarlavha: {video_obj.title}\n"
                                       f"📅 Yuklangan: {video_obj.completed_at.strftime('%Y-%m-%d %H:%M')}"
                            )
                        await processing_msg.delete()
                except Exception as e:
                    await processing_msg.edit_text(
                        f"✅ Video downloaded successfully!\n\n"
                        f"🎥 Title: {video_obj.title}\n"
                        f"📁 File: {video_obj.filename}\n\n"
                        f"⚠️ Could not send file (too large or format issue)\n"
                        f"🌐 Access via web: http://127.0.0.1:8001/"
                    )
            else:
                error_msg = video_obj.error_message or "Noma'lum xatolik yuz berdi"
                await processing_msg.edit_text(
                    f"❌ Yuklab olish muvaffaqiyatsiz!\n\n"
                    f"📊 Platforma: {video_obj.platform.title()}\n"
                    f"⚠️ Xatolik: {error_msg}\n\n"
                    "URL ni tekshiring va qaytadan urinib ko'ring."
                )
        except Exception as e:
            logger.error(f"Error sending download result: {e}")
    
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
        print("🤖 Starting Social Media Downloader Bot...")
        print("📱 Qo'llab quvvatlanadi: Instagram, Facebook, TikTok, Pinterest")
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