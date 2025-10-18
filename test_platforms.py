#!/usr/bin/env python3
"""
Test script for multi-platform URL detection and validation
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'instagram_project.settings')
django.setup()

from downloader.utils import detect_platform, validate_url

def test_urls():
    """Test URL detection and validation for all platforms"""
    
    test_urls = {
        'instagram': [
            'https://www.instagram.com/p/ABC123/',
            'https://instagram.com/reel/XYZ789/',
            'https://www.instagram.com/stories/username/123456789/',
            'instagram.com/p/TEST123/',
        ],
        'facebook': [
            'https://www.facebook.com/watch/?v=123456789',
            'https://facebook.com/videos/123456789/',
            'https://fb.watch/abc123/',
            'https://m.facebook.com/user/videos/123456789/',
        ],
        'tiktok': [
            'https://www.tiktok.com/@username/video/123456789',
            'https://vm.tiktok.com/ABC123/',
            'https://tiktok.com/t/ABC123/',
            'https://m.tiktok.com/@user/video/987654321',
        ],
        'pinterest': [
            'https://www.pinterest.com/pin/123456789/',
            'https://pinterest.com/user/board/pin123/',
            'https://www.pinterest.co.uk/pin/987654321/',
        ],
        'unsupported': [
            'https://youtube.com/watch?v=123',
            'https://twitter.com/user/status/123',
            'https://example.com/video.mp4',
            'not-a-url-at-all',
        ]
    }
    
    print("🧪 Testing Multi-Platform URL Detection & Validation\n")
    print("=" * 60)
    
    for expected_platform, urls in test_urls.items():
        print(f"\n📱 Testing {expected_platform.upper()} URLs:")
        print("-" * 40)
        
        for url in urls:
            detected_platform = detect_platform(url)
            is_valid, message = validate_url(url)
            
            status = "✅" if detected_platform == expected_platform else "❌"
            validation_status = "✅" if is_valid else "❌"
            
            print(f"{status} {url}")
            print(f"   Detected: {detected_platform}")
            print(f"   Valid: {validation_status} {message}")
            print()

def test_platform_configs():
    """Test platform-specific configurations"""
    from downloader.utils import get_platform_config
    
    print("\n🔧 Testing Platform Configurations:")
    print("=" * 60)
    
    platforms = ['instagram', 'facebook', 'tiktok', 'pinterest']
    
    for platform in platforms:
        config = get_platform_config(platform)
        print(f"\n📱 {platform.upper()} Configuration:")
        print(f"   User-Agent: {config.get('http_headers', {}).get('User-Agent', 'Default')[:50]}...")
        print(f"   Write Info JSON: {config.get('writeinfojson', 'N/A')}")
        print(f"   No Warnings: {config.get('no_warnings', 'N/A')}")

if __name__ == "__main__":
    test_urls()
    test_platform_configs()
    print("\n✨ Test completed!")