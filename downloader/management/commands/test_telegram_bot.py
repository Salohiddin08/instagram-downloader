from django.core.management.base import BaseCommand
from django.conf import settings
from downloader.telegram_utils import telegram_service
from downloader.models import TelegramUser
import asyncio

class Command(BaseCommand):
    help = 'Test Telegram bot connection and functionality'

    def add_arguments(self, parser):
        parser.add_argument(
            '--check-users',
            action='store_true',
            help='Check registered Telegram users'
        )
        parser.add_argument(
            '--send-test-message',
            type=str,
            help='Send test message to telegram ID'
        )

    def handle(self, *args, **options):
        self.stdout.write("🤖 Testing Telegram Bot Configuration\n")
        
        # Check bot token
        bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
        if not bot_token:
            self.stdout.write(
                self.style.ERROR("❌ TELEGRAM_BOT_TOKEN not found in settings")
            )
            return
        
        self.stdout.write(
            self.style.SUCCESS(f"✅ Bot token found: {bot_token[:10]}...{bot_token[-5:]}")
        )
        
        # Check bot connection
        try:
            bot = telegram_service.bot
            if bot:
                # Test bot connection with async call
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    bot_info = loop.run_until_complete(bot.get_me())
                    self.stdout.write(
                        self.style.SUCCESS(f"✅ Bot connected: @{bot_info.username}")
                    )
                    self.stdout.write(f"   Bot name: {bot_info.first_name}")
                    self.stdout.write(f"   Bot ID: {bot_info.id}")
                finally:
                    loop.close()
            else:
                self.stdout.write(
                    self.style.ERROR("❌ Bot instance not created")
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Bot connection failed: {e}")
            )
        
        # Check registered users
        if options['check_users']:
            self.stdout.write("\n📊 Registered Telegram Users:")
            users = TelegramUser.objects.all()
            if users.exists():
                for user in users:
                    self.stdout.write(
                        f"   📱 {user.phone_number} -> Telegram ID: {user.telegram_id}"
                    )
                    self.stdout.write(
                        f"      User: {user.user.username} | Verified: {user.is_verified}"
                    )
            else:
                self.stdout.write("   No registered users found")
        
        # Send test message
        if options['send_test_message']:
            telegram_id = options['send_test_message']
            self.stdout.write(f"\n📤 Sending test message to {telegram_id}...")
            
            try:
                success = telegram_service.send_otp_sync(
                    int(telegram_id), 
                    "123456", 
                    "test"
                )
                if success:
                    self.stdout.write(
                        self.style.SUCCESS("✅ Test message sent successfully")
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR("❌ Failed to send test message")
                    )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"❌ Error sending test message: {e}")
                )
        
        self.stdout.write("\n🏁 Telegram bot test completed!")