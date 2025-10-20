#!/usr/bin/env python3
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'instagram_project.settings')
django.setup()

from downloader.models import TelegramOTP, TelegramUser
from downloader.telegram_utils import telegram_service
from django.utils import timezone

def test_otp_flow():
    """Test the complete OTP flow"""
    phone_number = "+998338570052"  # The phone number from the logs
    
    print(f"Testing OTP flow for {phone_number}")
    
    # Step 1: Create OTP
    print("\n1. Creating OTP...")
    otp, error_message = telegram_service.create_otp_for_phone_number(phone_number)
    
    if otp:
        print(f"   ✅ OTP created: {otp.otp_code}")
        print(f"   Created: {otp.created_at}")
        print(f"   Expires: {otp.expires_at}")
        print(f"   Valid: {otp.is_valid()}")
        
        # Step 2: Test verification
        print(f"\n2. Testing verification with code: {otp.otp_code}")
        is_valid, message = telegram_service.verify_otp(phone_number, otp.otp_code)
        print(f"   Valid: {is_valid}")
        print(f"   Message: {message}")
        
        if is_valid:
            # Step 3: Test user creation
            print(f"\n3. Testing user creation...")
            user, user_message = telegram_service.get_or_create_user_from_phone(phone_number)
            print(f"   User: {user}")
            print(f"   Message: {user_message}")
    else:
        print(f"   ❌ Failed to create OTP: {error_message}")

    # Check Telegram user exists
    print(f"\n4. Checking Telegram user for {phone_number}")
    try:
        tg_user = TelegramUser.objects.get(phone_number=phone_number)
        print(f"   ✅ Found: {tg_user}")
        print(f"   Telegram ID: {tg_user.telegram_id}")
        print(f"   Verified: {tg_user.is_verified}")
    except TelegramUser.DoesNotExist:
        print(f"   ❌ No Telegram user found")

if __name__ == "__main__":
    test_otp_flow()