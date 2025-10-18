#!/usr/bin/env python3
"""
Test script for Pinterest pin.it URL support
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'instagram_project.settings')
django.setup()

from downloader.utils import detect_platform, validate_url

def test_pinterest_urls():
    """Test Pinterest URL detection including pin.it"""
    
    test_urls = [
        'https://pin.it/auBjfMjN2',
        'https://www.pin.it/auBjfMjN2',
        'pin.it/auBjfMjN2',
        'https://www.pinterest.com/pin/123456789/',
        'https://pinterest.com/pin/456789123/',
    ]
    
    print("🧪 Testing Pinterest URL Detection\n")
    print("=" * 50)
    
    for url in test_urls:
        platform = detect_platform(url)
        is_valid, message = validate_url(url, platform)
        
        status = "✅" if platform == 'pinterest' else "❌"
        validation_status = "✅" if is_valid else "❌"
        
        print(f"{status} URL: {url}")
        print(f"   Platform detected: {platform}")
        print(f"   Valid: {validation_status} {message}")
        print()
    
    print("✨ Pinterest URL test completed!")

if __name__ == "__main__":
    test_pinterest_urls()