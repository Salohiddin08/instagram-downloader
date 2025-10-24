"""
Advanced Instagram downloader with hosting-specific bypass techniques
Designed to work on PythonAnywhere and other hosting platforms
"""

import requests
import re
import json
import time
import random
from urllib.parse import quote, unquote
from django.conf import settings


def get_random_mobile_headers():
    """Get randomized mobile headers that work better on hosting platforms"""
    user_agents = [
        'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
        'Mozilla/5.0 (Linux; Android 12; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Mobile Safari/537.36',
        'Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Mobile Safari/537.36',
    ]
    
    return {
        'User-Agent': random.choice(user_agents),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0'
    }


def extract_shortcode_from_url(url):
    """Extract Instagram shortcode from various URL formats"""
    patterns = [
        r'instagram\.com/(?:p|reel|tv)/([A-Za-z0-9_-]+)',
        r'instagram\.com/(?:p|reel|tv)/([A-Za-z0-9_-]+)/',
        r'/([A-Za-z0-9_-]+)/?(?:\?.*)?$'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def try_direct_api_bypass(shortcode):
    """
    Try to extract Instagram content using direct API calls
    This method works better on hosting platforms
    """
    try:
        # Method 1: Try the embed endpoint
        embed_url = f"https://www.instagram.com/p/{shortcode}/embed"
        
        session = requests.Session()
        session.headers.update(get_random_mobile_headers())
        
        # Add random delay
        time.sleep(random.uniform(1, 3))
        
        response = session.get(embed_url, timeout=30)
        if response.status_code == 200:
            content = response.text
            
            # Extract JSON data from embed page
            json_pattern = r'window\._sharedData\s*=\s*({.+?});'
            match = re.search(json_pattern, content)
            
            if match:
                try:
                    data = json.loads(match.group(1))
                    media_info = extract_media_from_shared_data(data, shortcode)
                    if media_info:
                        return media_info
                except json.JSONDecodeError:
                    pass
        
        # Method 2: Try mobile endpoint
        mobile_url = f"https://www.instagram.com/p/{shortcode}/?__a=1&__d=dis"
        
        mobile_headers = get_random_mobile_headers()
        mobile_headers.update({
            'X-Requested-With': 'XMLHttpRequest',
            'X-Instagram-AJAX': '1',
            'X-CSRFToken': 'missing',
        })
        
        time.sleep(random.uniform(2, 4))
        
        response = session.get(mobile_url, headers=mobile_headers, timeout=30)
        if response.status_code == 200:
            try:
                data = response.json()
                media_info = extract_media_from_api_response(data, shortcode)
                if media_info:
                    return media_info
            except (json.JSONDecodeError, ValueError):
                pass
                
        return None
        
    except Exception as e:
        return None


def extract_media_from_shared_data(data, shortcode):
    """Extract media URLs from Instagram's _sharedData"""
    try:
        # Navigate through the nested structure
        entry_data = data.get('entry_data', {})
        post_page = entry_data.get('PostPage', [])
        
        if not post_page:
            return None
            
        media = post_page[0].get('graphql', {}).get('shortcode_media', {})
        
        if not media:
            return None
            
        # Extract basic info
        media_info = {
            'title': media.get('edge_media_to_caption', {}).get('edges', [{}])[0].get('node', {}).get('text', ''),
            'is_video': media.get('is_video', False),
            'media_type': 'video' if media.get('is_video') else 'image'
        }
        
        if media_info['is_video']:
            media_info['video_url'] = media.get('video_url')
        else:
            media_info['image_url'] = media.get('display_url')
            
        # Try to get thumbnail
        media_info['thumbnail'] = media.get('display_url')
        
        return media_info if (media_info.get('video_url') or media_info.get('image_url')) else None
        
    except Exception:
        return None


def extract_media_from_api_response(data, shortcode):
    """Extract media URLs from Instagram API response"""
    try:
        items = data.get('items', [])
        if not items:
            return None
            
        media = items[0]
        
        media_info = {
            'title': media.get('caption', {}).get('text', '') if media.get('caption') else '',
            'media_type': 'video' if media.get('media_type') == 2 else 'image'
        }
        
        if media.get('media_type') == 2:  # Video
            media_info['is_video'] = True
            video_versions = media.get('video_versions', [])
            if video_versions:
                # Get the lowest quality for hosting compatibility
                video_url = min(video_versions, key=lambda x: x.get('width', 0) * x.get('height', 0))
                media_info['video_url'] = video_url.get('url')
        else:  # Image
            media_info['is_video'] = False
            candidates = media.get('image_versions2', {}).get('candidates', [])
            if candidates:
                # Get the highest quality image
                image_url = max(candidates, key=lambda x: x.get('width', 0) * x.get('height', 0))
                media_info['image_url'] = image_url.get('url')
        
        # Thumbnail
        candidates = media.get('image_versions2', {}).get('candidates', [])
        if candidates:
            media_info['thumbnail'] = candidates[0].get('url')
            
        return media_info if (media_info.get('video_url') or media_info.get('image_url')) else None
        
    except Exception:
        return None


def download_instagram_content_bypass(video_obj):
    """
    Main function to download Instagram content with bypass techniques
    Specifically designed for hosting environments
    """
    try:
        from .utils import download_image_from_url
        from django.utils import timezone
        import os
        
        # Extract shortcode from URL
        shortcode = extract_shortcode_from_url(video_obj.url)
        if not shortcode:
            return False, "Invalid Instagram URL format"
            
        # Try direct API bypass first
        media_info = try_direct_api_bypass(shortcode)
        
        if not media_info:
            return False, "Could not extract media information"
            
        # Update video object with extracted info
        video_obj.title = media_info.get('title', 'Instagram Content')[:200]  # Limit length
        video_obj.media_type = media_info['media_type']
        video_obj.status = 'downloading'
        video_obj.save()
        
        # Create media directory
        media_path = os.path.join(settings.MEDIA_ROOT, 'downloads', video_obj.platform)
        os.makedirs(media_path, exist_ok=True)
        
        # Download the actual content
        if media_info['is_video'] and media_info.get('video_url'):
            success = download_media_file(
                video_obj, 
                media_info['video_url'], 
                media_path,
                'mp4'
            )
        elif media_info.get('image_url'):
            success = download_media_file(
                video_obj, 
                media_info['image_url'], 
                media_path,
                'jpg'
            )
        else:
            return False, "No downloadable media found"
            
        if success:
            video_obj.status = 'completed'
            video_obj.completed_at = timezone.now()
            video_obj.save()
            return True, "Download completed successfully"
        else:
            return False, "Failed to download media file"
            
    except Exception as e:
        return False, f"Download error: {str(e)}"


def download_media_file(video_obj, media_url, media_path, extension):
    """Download media file from direct URL with hosting-optimized settings"""
    try:
        import os
        
        # Create session with optimal settings for hosting
        session = requests.Session()
        session.headers.update(get_random_mobile_headers())
        
        # Add random delay to avoid rate limiting
        time.sleep(random.uniform(2, 5))
        
        # Download with streaming for large files
        response = session.get(
            media_url, 
            stream=True, 
            timeout=(30, 300),  # (connect timeout, read timeout)
            headers={
                'Range': 'bytes=0-',  # Request full file
                'Referer': 'https://www.instagram.com/'
            }
        )
        
        response.raise_for_status()
        
        # Create safe filename
        safe_title = "".join(c for c in video_obj.title if c.isalnum() or c in (' ', '-', '_')).rstrip()[:50]
        if not safe_title:
            safe_title = f"instagram_content_{int(time.time())}"
            
        filename = f"{safe_title}.{extension}"
        file_path = os.path.join(media_path, filename)
        
        # Download in chunks to handle large files on hosting
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        # Verify file was downloaded
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            video_obj.filename = filename
            video_obj.file_path = file_path
            return True
        else:
            return False
            
    except Exception as e:
        return False