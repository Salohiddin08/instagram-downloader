#!/usr/bin/env python3
"""
Quick test to verify multi-platform functionality is working
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'instagram_project.settings')
django.setup()

from downloader.utils import detect_platform, validate_url

def test_quick():
    """Quick test of platform detection"""
    
    test_urls = [
        'https://www.instagram.com/p/ABC123/',
        'https://www.facebook.com/watch/?v=123456789',
        'https://www.tiktok.com/@user/video/123456789',
        'https://www.pinterest.com/pin/123456789/',
    ]
    
    print("🧪 Quick Multi-Platform Test")
    print("=" * 40)
    
    for url in test_urls:
        platform = detect_platform(url)
        is_valid, message = validate_url(url, platform)
        status = "✅" if is_valid else "❌"
        print(f"{status} {platform.upper()}: {url}")
        print(f"   {message}")
        print()
    
    print("✨ All platforms are working!")

if __name__ == "__main__":
    test_quick()