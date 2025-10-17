#!/usr/bin/env python3
"""
Telegram Bot Setup Script for Instagram Downloader

This script helps you set up a Telegram bot for authentication.

Usage:
1. Create a bot with @BotFather on Telegram
2. Get your bot token
3. Run: python telegram_bot_setup.py YOUR_BOT_TOKEN
4. Update your Django settings with the bot token
"""

import os
import sys
import asyncio
from telegram import Bot
from telegram.error import TelegramError

async def setup_bot(bot_token):
    """Set up and test the Telegram bot"""
    try:
        bot = Bot(token=bot_token)
        
        # Get bot info
        print("🤖 Testing bot connection...")
        me = await bot.get_me()
        
        print(f"✅ Bot connected successfully!")
        print(f"   Bot Name: {me.first_name}")
        print(f"   Username: @{me.username}")
        print(f"   Bot ID: {me.id}")
        
        # Set bot commands
        commands = [
            ("start", "Get your Telegram ID for login"),
            ("id", "Get your Telegram ID"),
            ("help", "Show help information"),
        ]
        
        print("🔧 Setting up bot commands...")
        await bot.set_my_commands(commands)
        print("✅ Bot commands set successfully!")
        
        print(f"\n📋 Next steps:")
        print(f"1. Add this to your Django settings.py:")
        print(f"   TELEGRAM_BOT_TOKEN = '{bot_token}'")
        print(f"   TELEGRAM_BOT_USERNAME = '{me.username}'")
        print(f"\n2. Update the template at:")
        print(f"   downloader/templates/registration/telegram_login.html")
        print(f"   Replace 'YOUR_BOT_USERNAME' with '{me.username}'")
        print(f"\n3. Start your Django server and test the Telegram login!")
        
        return me
        
    except TelegramError as e:
        print(f"❌ Telegram API Error: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

def main():
    if len(sys.argv) != 2:
        print("Usage: python telegram_bot_setup.py YOUR_BOT_TOKEN")
        print("\nTo get a bot token:")
        print("1. Message @BotFather on Telegram")
        print("2. Send /newbot")
        print("3. Follow the instructions")
        print("4. Copy the token and run this script")
        sys.exit(1)
    
    bot_token = sys.argv[1]
    
    print("🚀 Setting up Telegram bot for Instagram Downloader...")
    
    # Run the async setup
    bot_info = asyncio.run(setup_bot(bot_token))
    
    if bot_info:
        print("🎉 Setup completed successfully!")
    else:
        print("💥 Setup failed. Please check your bot token and try again.")
        sys.exit(1)

if __name__ == "__main__":
    main()