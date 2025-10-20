#!/usr/bin/env python3
"""
Production deployment test script for PythonAnywhere
Tests Telegram authentication and video download functionality
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'instagram_project.settings')
django.setup()

from downloader.telegram_utils import TelegramAuthService
from downloader.utils import detect_platform, validate_url, get_platform_config
from downloader.models import TelegramUser, DownloadedVideo
from django.contrib.auth.models import User
import yt_dlp
import requests

def test_telegram_api():
    """Test Telegram API connectivity"""
    print("🤖 Testing Telegram API...")
    
    service = TelegramAuthService()
    if not service.bot_token:
        print("❌ Telegram bot token not configured")
        return False
    
    # Test bot info
    try:
        url = f"https://api.telegram.org/bot{service.bot_token}/getMe"
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                bot_info = result.get('result', {})
                print(f"✅ Bot connected: @{bot_info.get('username')}")
                return True
        
        print(f"❌ Bot API error: HTTP {response.status_code}")
        return False
        
    except Exception as e:
        print(f"❌ Bot API connection failed: {e}")
        return False

def test_video_download():
    """Test video download functionality"""
    print("\n📹 Testing video download...")
    
    # Test URL validation
    test_urls = [
        "https://www.instagram.com/p/test123/",
        "https://www.tiktok.com/@user/video/1234567890",
        "https://www.facebook.com/watch/?v=1234567890"
    ]
    
    for url in test_urls:
        platform = detect_platform(url)
        is_valid, message = validate_url(url, platform)
        print(f"  {platform}: {'✅' if is_valid else '❌'} {message}")
    
    # Test yt-dlp configuration
    try:
        config = get_platform_config('instagram')
        print("✅ yt-dlp configuration loaded")
        
        # Test yt-dlp with a simple URL (won't actually download)
        with yt_dlp.YoutubeDL(config) as ydl:
            # Test if yt-dlp can initialize without errors
            print("✅ yt-dlp initialized successfully")
            
    except Exception as e:
        print(f"❌ yt-dlp error: {e}")
        return False
    
    return True

def test_database():
    """Test database connectivity"""
    print("\n🗄️ Testing database...")
    
    try:
        # Test basic queries
        user_count = User.objects.count()
        telegram_user_count = TelegramUser.objects.count()
        video_count = DownloadedVideo.objects.count()
        
        print(f"✅ Database connected")
        print(f"  Users: {user_count}")
        print(f"  Telegram Users: {telegram_user_count}")
        print(f"  Downloaded Videos: {video_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def test_media_directories():
    """Test media directory setup"""
    print("\n📁 Testing media directories...")
    
    from django.conf import settings
    
    try:
        media_root = settings.MEDIA_ROOT
        print(f"Media root: {media_root}")
        
        required_dirs = [
            'downloads',
            'downloads/instagram',
            'downloads/facebook',
            'downloads/tiktok',
            'downloads/pinterest'
        ]
        
        for dir_name in required_dirs:
            full_path = os.path.join(media_root, dir_name)
            if os.path.exists(full_path):
                print(f"✅ {dir_name}")
            else:
                print(f"❌ {dir_name} (missing)")
                # Try to create it
                try:
                    os.makedirs(full_path, exist_ok=True)
                    print(f"✅ Created {dir_name}")
                except Exception as e:
                    print(f"❌ Failed to create {dir_name}: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Media directory error: {e}")
        return False

def test_external_requests():
    """Test external HTTP requests (important for PythonAnywhere)"""
    print("\n🌐 Testing external requests...")
    
    test_sites = [
        "https://api.telegram.org",
        "https://www.instagram.com",
        "https://www.youtube.com"
    ]
    
    all_successful = True
    
    for site in test_sites:
        try:
            response = requests.get(site, timeout=10)
            if response.status_code < 400:
                print(f"  ✅ {site}: HTTP {response.status_code}")
            else:
                print(f"  ⚠️ {site}: HTTP {response.status_code}")
                all_successful = False
        except Exception as e:
            print(f"  ❌ {site}: {e}")
            all_successful = False
    
    return all_successful

def main():
    """Run all tests"""
    print("🔍 Production Deployment Test Suite")
    print("=" * 50)
    
    tests = [
        ("Database", test_database),
        ("Media Directories", test_media_directories),
        ("Telegram API", test_telegram_api),
        ("Video Download", test_video_download),
        ("External Requests", test_external_requests)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results[test_name] = False
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}: {test_name}")
    
    all_passed = all(results.values())
    print(f"\n🎯 Overall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    if not all_passed:
        print("\n💡 Check the DEPLOYMENT_GUIDE.md for solutions to failed tests.")

if __name__ == "__main__":
    main()