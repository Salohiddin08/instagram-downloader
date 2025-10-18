#!/usr/bin/env python3
"""
Test script for image downloading functionality
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'instagram_project.settings')
django.setup()

from downloader.models import DownloadedVideo
from downloader.utils import download_video, detect_platform
from django.contrib.auth.models import User

def test_image_download():
    """Test image downloading with sample URLs"""
    
    # Create test user if not exists
    user, created = User.objects.get_or_create(username='testuser')
    if created:
        user.set_password('testpass')
        user.save()
        print("✅ Created test user")
    
    # Test URLs for different platforms
    test_urls = [
        'https://www.pinterest.com/pin/123456789/',  # Pinterest image
        'https://www.instagram.com/p/test123/',      # Instagram image
    ]
    
    print("🧪 Testing Image Download Functionality\n")
    print("=" * 50)
    
    for url in test_urls:
        platform = detect_platform(url)
        print(f"\n📱 Testing {platform.upper()}: {url}")
        
        # Create download record
        video_obj = DownloadedVideo.objects.create(
            user=user,
            url=url,
            platform=platform,
            title='Test Download',
            status='pending'
        )
        
        print(f"   Created download record ID: {video_obj.id}")
        print("   Status: Attempting download...")
        
        # Attempt download
        try:
            result = download_video(video_obj)
            video_obj.refresh_from_db()
            
            if video_obj.status == 'completed':
                print(f"   ✅ SUCCESS: {video_obj.media_type} downloaded")
                print(f"   📁 File: {video_obj.filename}")
                print(f"   📏 Size: {os.path.getsize(video_obj.file_path) / 1024:.2f} KB" if video_obj.file_path and os.path.exists(video_obj.file_path) else "   📏 File not found")
            else:
                print(f"   ❌ FAILED: {video_obj.error_message}")
        except Exception as e:
            print(f"   💥 ERROR: {str(e)}")
        
        print("-" * 40)

if __name__ == "__main__":
    test_image_download()
    print("\n🏁 Image download test completed!")