import asyncio
import logging
from django.conf import settings
from django.utils import timezone
from telegram import Bot
from telegram.error import TelegramError
from .models import TelegramOTP, TelegramUser
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)


class TelegramAuthService:
    """Service class for handling Telegram authentication"""
    
    def __init__(self):
        self.bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
        self.bot = None
        if self.bot_token:
            self.bot = Bot(token=self.bot_token)
    
    async def send_otp_to_telegram(self, telegram_id, otp_code, phone_number=None):
        """Send OTP code to user via Telegram bot"""
        if not self.bot:
            logger.error("Telegram bot token not configured")
            return False
        
        try:
            message = f"🔐 Social Media Downloader uchun kirish kodingiz:\n\n" \
                     f"**{otp_code}**\n\n" \
                     f"Bu kod 10 daqiqada muddati tugaydi.\n" \
                     f"Bu kodni hech kimga bermang!"
            
            await self.bot.send_message(
                chat_id=telegram_id,
                text=message,
                parse_mode='Markdown'
            )
            logger.info(f"OTP sent successfully to Telegram ID: {telegram_id}")
            return True
            
        except TelegramError as e:
            logger.error(f"Failed to send OTP to Telegram ID {telegram_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending OTP: {e}")
            return False
    
    def send_otp_sync(self, telegram_id, otp_code, phone_number=None):
        """Synchronous wrapper for sending OTP"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(
                self.send_otp_to_telegram(telegram_id, otp_code, phone_number)
            )
        finally:
            loop.close()
    
    def create_otp_for_phone_number(self, phone_number):
        """Create a new OTP for the given phone number"""
        try:
            # Find Telegram user by phone number
            telegram_user = TelegramUser.objects.filter(phone_number=phone_number).first()
            
            if not telegram_user:
                logger.error(f"No Telegram user found for phone number: {phone_number}")
                return None, "Telefon raqami ro'yxatdan o'tmagan. Iltimos, avval botimizga xabar yozing va ro'yxatdan o'ting."
            
            if not telegram_user.telegram_id:
                logger.error(f"Telegram ID not found for phone number: {phone_number}")
                return None, "Telegram ID topilmadi. Iltimos, botda qaytadan ro'yxatdan o'ting."
            
            telegram_id = telegram_user.telegram_id
            
            # Invalidate any existing unused OTPs for this phone number
            TelegramOTP.objects.filter(
                phone_number=phone_number,
                is_used=False
            ).update(is_used=True)
            
            # Create new OTP
            otp = TelegramOTP.objects.create(
                telegram_id=telegram_id,
                phone_number=phone_number,
                expires_at=timezone.now() + timezone.timedelta(minutes=10)
            )
            
            # Send OTP via Telegram
            success = self.send_otp_sync(telegram_id, otp.otp_code, phone_number)
            
            if success:
                logger.info(f"OTP created and sent for phone number: {phone_number}")
                return otp, None
            else:
                # If sending failed, mark OTP as used
                otp.is_used = True
                otp.save()
                logger.error(f"Failed to send OTP for phone number: {phone_number}")
                return None, "OTP yuborishda xatolik. Iltimos, qaytadan urinib ko'ring. Botni ishga tushirganingizga ishonch hosil qiling."
                
        except Exception as e:
            logger.error(f"Error creating OTP for phone number {phone_number}: {e}")
            return None, "An error occurred. Please try again."
    
    def verify_otp(self, phone_number, otp_code):
        """Verify the OTP code for a phone number"""
        try:
            otp = TelegramOTP.objects.filter(
                phone_number=phone_number,
                otp_code=otp_code,
                is_used=False
            ).first()
            
            if not otp:
                logger.warning(f"OTP not found for phone number: {phone_number}")
                return False, "Noto'g'ri OTP kod"
            
            # Increment attempts
            otp.attempts += 1
            otp.save()
            
            if not otp.is_valid():
                if otp.is_expired():
                    return False, "OTP kodining muddati tugagan"
                elif otp.attempts >= otp.max_attempts:
                    return False, "Juda ko'p urinish. Iltimos, yangi kod so'rang"
                else:
                    return False, "Noto'g'ri OTP kod"
            
            # Mark OTP as used
            otp.is_used = True
            otp.save()
            
            logger.info(f"OTP verified successfully for phone number: {phone_number}")
            return True, "OTP muvaffaqiyatli tasdiqlandi"
            
        except Exception as e:
            logger.error(f"Error verifying OTP for phone number {phone_number}: {e}")
            return False, "An error occurred during verification"
    
    def get_or_create_user_from_phone(self, phone_number):
        """Get or create Django user from phone number"""
        try:
            # Try to find existing Telegram user by phone
            try:
                telegram_user = TelegramUser.objects.get(phone_number=phone_number)
                return telegram_user.user, "Existing user found"
            except TelegramUser.DoesNotExist:
                pass
            
            # Create new user with phone number
            username = f"user_{phone_number.replace('+', '').replace('-', '').replace(' ', '')}"
            
            # Ensure unique username
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}_{counter}"
                counter += 1
            
            # Create Django user
            user = User.objects.create_user(
                username=username,
                first_name=phone_number,  # Use phone as first name temporarily
                email=f"{username}@telegram.local"  # Placeholder email
            )
            
            # Create Telegram user profile with phone number
            telegram_user = TelegramUser.objects.create(
                user=user,
                telegram_id=0,  # Will be updated when user messages the bot
                phone_number=phone_number,
                is_verified=True
            )
            
            logger.info(f"New user created from phone: {phone_number}")
            return user, "New user created successfully"
            
        except Exception as e:
            logger.error(f"Error creating user from phone data: {e}")
            return None, "Error creating user account"
    
    async def get_telegram_user_info(self, telegram_id):
        """Get user information from Telegram API"""
        if not self.bot:
            return None
        
        try:
            user = await self.bot.get_chat(chat_id=telegram_id)
            return {
                'id': user.id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'type': user.type
            }
        except TelegramError as e:
            logger.error(f"Failed to get Telegram user info for ID {telegram_id}: {e}")
            return None


# Global service instance
telegram_service = TelegramAuthService()