#!/usr/bin/env python
"""
Test script for Instagram downloader improvements
Run this to test if the hosting fixes work
"""

import os
import sys
import django
from django.conf import settings

# Setup Django environment
sys.path.append('/home/salohiddin/insta/instagram-downloader')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'instagram_project.settings')
django.setup()

from downloader.models import DownloadedVideo
from downloader.utils import download_video, detect_platform
from downloader.instagram_bypass import download_instagram_content_bypass, extract_shortcode_from_url
from django.contrib.auth.models import User


def test_instagram_download():
    """Test Instagram download with the example URL provided"""
    
    # Test URL from the user's issue
    test_url = "https://www.instagram.com/reel/DMahSXOIzzB/?utm_source=ig_web_copy_link"
    
    print(f"Testing Instagram download with URL: {test_url}")
    print("-" * 60)
    
    # Test shortcode extraction
    shortcode = extract_shortcode_from_url(test_url)
    print(f"Extracted shortcode: {shortcode}")
    
    # Test platform detection
    platform = detect_platform(test_url)
    print(f"Detected platform: {platform}")
    
    # Get or create a test user
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={'email': 'test@example.com'}
    )
    if created:
        print("Created test user")
    
    # Create a test video object
    video_obj = DownloadedVideo.objects.create(
        user=user,
        url=test_url,
        platform=platform,
        status='pending'
    )
    print(f"Created video object ID: {video_obj.id}")
    
    # Test bypass method first
    print("\n1. Testing bypass method...")
    bypass_success, bypass_message = download_instagram_content_bypass(video_obj)
    print(f"Bypass result: {bypass_success}")
    print(f"Bypass message: {bypass_message}")
    
    if bypass_success:
        print("✅ Bypass method succeeded!")
        print(f"Title: {video_obj.title}")
        print(f"Media type: {video_obj.media_type}")
        print(f"Status: {video_obj.status}")
        if video_obj.file_path:
            print(f"File path: {video_obj.file_path}")
            print(f"File exists: {os.path.exists(video_obj.file_path) if video_obj.file_path else 'No file path'}")
    else:
        print("❌ Bypass method failed, testing standard method...")
        
        # Test standard method
        print("\n2. Testing standard method...")
        result_video = download_video(video_obj)
        
        print(f"Standard result status: {result_video.status}")
        print(f"Error message: {result_video.error_message}")
        
        if result_video.status == 'completed':
            print("✅ Standard method succeeded!")
            print(f"Title: {result_video.title}")
            print(f"Media type: {result_video.media_type}")
            if result_video.file_path:
                print(f"File path: {result_video.file_path}")
                print(f"File exists: {os.path.exists(result_video.file_path) if result_video.file_path else 'No file path'}")
        else:
            print("❌ Standard method also failed")
    
    print("\n" + "=" * 60)
    print("Test completed!")


def test_facebook_download():
    """Test Facebook download with the example URL provided"""
    
    # Test Facebook URL from the user's issue
    test_url = "https://www.facebook.com/share/r/1BaTsZn6Qb/"
    
    print(f"\nTesting Facebook download with URL: {test_url}")
    print("-" * 60)
    
    # Test platform detection
    platform = detect_platform(test_url)
    print(f"Detected platform: {platform}")
    
    if platform == 'other':
        print("❌ Facebook URL not recognized, checking pattern...")
        # Add Facebook pattern test here
        
    # Get test user
    user = User.objects.get(username='testuser')
    
    # Create a test video object
    video_obj = DownloadedVideo.objects.create(
        user=user,
        url=test_url,
        platform=platform if platform != 'other' else 'facebook',
        status='pending'
    )
    print(f"Created video object ID: {video_obj.id}")
    
    # Test download
    result_video = download_video(video_obj)
    
    print(f"Facebook result status: {result_video.status}")
    print(f"Error message: {result_video.error_message}")
    
    if result_video.status == 'completed':
        print("✅ Facebook download succeeded!")
        print(f"Title: {result_video.title}")
        print(f"Media type: {result_video.media_type}")
    else:
        print("❌ Facebook download failed")


if __name__ == "__main__":
    print("Instagram/Facebook Downloader Test")
    print("=" * 60)
    
    # Test Instagram first
    test_instagram_download()
    
    # Test Facebook
    test_facebook_download()
    
    print(f"\nTest environment: DEBUG = {settings.DEBUG}")
    print("Note: If DEBUG=False, the system will use production optimizations")