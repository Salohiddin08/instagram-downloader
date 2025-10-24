import os
import re
import requests
import yt_dlp
from django.conf import settings
from django.utils import timezone
from .models import DownloadedVideo
from urllib.parse import urlparse
from PIL import Image


# Platform detection patterns
PLATFORM_PATTERNS = {
    'instagram': [
        r'(?:https?://)?(?:www\.)?instagram\.com/(?:p|reel|tv)/([A-Za-z0-9_-]+)/?',
        r'(?:https?://)?(?:www\.)?instagram\.com/stories/[^/]+/([0-9]+)/?'
    ],
    'facebook': [
        r'(?:https?://)?(?:www\.|m\.)?facebook\.com/.*/videos?/([0-9]+)/?',
        r'(?:https?://)?(?:www\.|m\.)?facebook\.com/watch/\?v=([0-9]+)',
        r'(?:https?://)?fb\.watch/([A-Za-z0-9_-]+)/?',
        r'(?:https?://)?(?:www\.|m\.)?facebook\.com/share/r/([A-Za-z0-9_-]+)/?',
        r'(?:https?://)?(?:www\.|m\.)?facebook\.com/share/v/([A-Za-z0-9_-]+)/?'
    ],
    'tiktok': [
        r'(?:https?://)?(?:www\.|vm\.|m\.)?tiktok\.com/@[^/]+/video/([0-9]+)/?',
        r'(?:https?://)?(?:www\.|vm\.|m\.)?tiktok\.com/t/([A-Za-z0-9_-]+)/?',
        r'(?:https?://)?vm\.tiktok\.com/([A-Za-z0-9_-]+)/?'
    ],
    'pinterest': [
        r'(?:https?://)?(?:www\.)?pinterest\.[^/]+/pin/([0-9]+)/?',
        r'(?:https?://)?(?:www\.)?pinterest\.[^/]+/[^/]+/[^/]+/([A-Za-z0-9_-]+)/?',
        r'(?:https?://)?(?:www\.)?pinterest\.[^/]+/.*',
        r'(?:https?://)?pin\.it/([A-Za-z0-9_-]+)/?',  # Pinterest short URLs
        r'(?:https?://)?(?:www\.)?pin\.it/([A-Za-z0-9_-]+)/?'  # Alternative pin.it format
    ]
}


def _get_random_instagram_headers():
    """
    Get random headers for Instagram to avoid detection
    Enhanced for hosting environments
    """
    import random
    
    # Updated and expanded user agents for better compatibility
    user_agents = [
        # Mobile agents (less likely to be blocked)
        'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
        'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
        'Mozilla/5.0 (Linux; Android 12; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Mobile Safari/537.36',
        'Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Mobile Safari/537.36',
        'Mozilla/5.0 (Linux; Android 11; SM-A515F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36',
        # Desktop agents for fallback
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
        # Instagram app user agents
        'Instagram 302.0.0.23.109 Android (33/13; 420dpi; 1080x2400; samsung; SM-G991B; o1s; qcom; en_US; 511558019)',
        'Instagram 300.1.0.23.111 Android (31/12; 440dpi; 1080x2340; xiaomi; M2102J20SG; alioth; qcom; en_US; 507075138)'
    ]
    
    # More comprehensive headers
    return {
        'User-Agent': random.choice(user_agents),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9,uz;q=0.8,ru;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
        'sec-ch-ua': '"Chromium";v="118", "Google Chrome";v="118", "Not=A?Brand";v="99"',
        'sec-ch-ua-mobile': random.choice(['?0', '?1']),
        'sec-ch-ua-platform': random.choice(['"Windows"', '"macOS"', '"Linux"', '"Android"'])
    }


def detect_platform(url):
    """
    Detect the platform from URL
    """
    for platform, patterns in PLATFORM_PATTERNS.items():
        for pattern in patterns:
            if re.match(pattern, url, re.IGNORECASE):
                return platform
    return 'other'


def validate_url(url, platform=None):
    """
    Validate URL format for specific platform
    """
    if not platform:
        platform = detect_platform(url)
    
    if platform == 'other':
        return False, "Unsupported platform. Supported: Instagram, Facebook, TikTok, Pinterest"
    
    patterns = PLATFORM_PATTERNS.get(platform, [])
    for pattern in patterns:
        if re.match(pattern, url, re.IGNORECASE):
            return True, f"Valid {platform.title()} URL"
    
    return False, f"Invalid {platform.title()} URL format"


def get_platform_config(platform):
    """
    Get platform-specific yt-dlp configuration
    Enhanced for hosting environments with better error handling
    """
    from django.conf import settings
    import random
    
    # Determine if we're in production (hosting)
    is_production = not getattr(settings, 'DEBUG', True)
    
    base_config = {
        'writeinfojson': False,
        'writesubtitles': False,
        'writeautomaticsub': False,
        'no_warnings': True,
        'ignoreerrors': False,
        'extractaudio': False,
        # Enhanced timeout settings for hosting
        'socket_timeout': 60 if is_production else 30,
        'retries': 5 if is_production else 3,
        # Force IPv4 for hosting compatibility (especially PythonAnywhere)
        'prefer_ipv4': True,
        # Add geo-bypass for restricted content
        'geo_bypass': True,
        'geo_bypass_country': 'US',
        # Add rate limiting to avoid blocks
        'sleep_interval': 2 if is_production else 1,
        'max_sleep_interval': 5 if is_production else 3,
        # Enable verbose logging for debugging on hosting
        'verbose': False,  # Keep false to avoid log spam
        # Add fragment retries for unstable connections
        'fragment_retries': 10,
        'skip_unavailable_fragments': True,
        # Add more robust error handling
        'continuedl': True,
        # Force TLS version for better compatibility
        'http_chunk_size': 10485760 if is_production else None,  # 10MB chunks for hosting
    }
    
    # Add proxy configuration for production environment (disabled for now)
    # from django.conf import settings
    # if not settings.DEBUG and platform == 'instagram':
    #     # Use real proxy servers here when available
    #     proxy_list = [
    #         # 'http://real-proxy1.com:8080',
    #         # 'http://real-proxy2.com:8080',
    #     ]
    #     import random
    #     if proxy_list:
    #         base_config['proxy'] = random.choice(proxy_list)
    
    platform_configs = {
        'instagram': {
            'http_headers': _get_random_instagram_headers(),
            # Enhanced Instagram options for hosting
            'sleep_interval': 3 if is_production else 1,
            'max_sleep_interval': 8 if is_production else 3,
            'extractor_args': {
                'instagram': {
                    'api_version': 'v1',
                    'include_stories': False,
                    'variant': 'mobile' if is_production else 'web',
                    'comment_count': 0,  # Disable comments to reduce load
                    'like_count': 0      # Disable likes to reduce load
                }
            },
            # Add cookies handling for better authentication
            'cookiefile': None,  # Don't use cookies to avoid issues
            # Additional Instagram-specific headers
            'http_headers': {
                **_get_random_instagram_headers(),
                'X-Instagram-AJAX': '1',
                'X-Requested-With': 'XMLHttpRequest'
            } if is_production else _get_random_instagram_headers(),
        },
        'facebook': {
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            },
        },
        'tiktok': {
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Mobile Safari/537.36'
            },
        },
        'pinterest': {
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            },
        }
    }
    
    config = base_config.copy()
    config.update(platform_configs.get(platform, {}))
    return config


def download_image_from_url(video_obj, image_url, title="Unknown"):
    """
    Download image from direct URL
    """
    try:
        # Create media directory
        media_path = os.path.join(settings.MEDIA_ROOT, 'downloads', video_obj.platform)
        os.makedirs(media_path, exist_ok=True)
        
        # Get image
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(image_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Determine file extension
        content_type = response.headers.get('content-type', '')
        if 'jpeg' in content_type or 'jpg' in content_type:
            ext = 'jpg'
        elif 'png' in content_type:
            ext = 'png'
        elif 'webp' in content_type:
            ext = 'webp'
        else:
            # Try to determine from URL
            parsed_url = urlparse(image_url)
            if parsed_url.path.endswith(('.jpg', '.jpeg', '.png', '.webp')):
                ext = parsed_url.path.split('.')[-1]
            else:
                ext = 'jpg'  # Default
        
        # Create filename
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()[:50]
        if not safe_title:
            safe_title = "image"
        
        filename = f"{safe_title}.{ext}"
        file_path = os.path.join(media_path, filename)
        
        # Save image
        with open(file_path, 'wb') as f:
            f.write(response.content)
        
        # Verify it's a valid image
        try:
            with Image.open(file_path) as img:
                img.verify()
        except Exception:
            # If verification fails, still consider it successful
            pass
        
        video_obj.filename = filename
        video_obj.file_path = file_path
        video_obj.title = title
        video_obj.media_type = 'image'
        video_obj.status = 'completed'
        video_obj.completed_at = timezone.now()
        video_obj.save()
        
        # Schedule automatic deletion after 10 minutes
        try:
            from .tasks import schedule_cleanup_after_download
            schedule_cleanup_after_download(video_obj.id, delay_minutes=10)
        except ImportError:
            # If Celery is not available, use simple threading approach
            import threading
            import time
            
            def delayed_cleanup():
                time.sleep(10 * 60)  # Wait 10 minutes
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        video_obj.file_path = ''
                        video_obj.filename = ''
                        video_obj.save()
                except Exception as e:
                    pass  # Silently ignore cleanup errors
            
            cleanup_thread = threading.Thread(target=delayed_cleanup, daemon=True)
            cleanup_thread.start()
        
        return True
        
    except Exception as e:
        video_obj.status = 'failed'
        video_obj.error_message = f'Rasm yuklab olishda xatolik: {str(e)}'
        video_obj.save()
        return False


def download_video(video_obj):
    """
    Universal video downloader that handles all supported platforms
    """
    try:
        # Update status to downloading
        video_obj.status = 'downloading'
        video_obj.save()
        
        # Detect platform if not set
        if not video_obj.platform or video_obj.platform == 'other':
            video_obj.platform = detect_platform(video_obj.url)
            video_obj.save()
        
        # Validate URL
        is_valid, message = validate_url(video_obj.url, video_obj.platform)
        if not is_valid:
            video_obj.status = 'failed'
            video_obj.error_message = message
            video_obj.save()
            return video_obj
        
        # Try to get media info first
        try:
            info_opts = {
                'quiet': True,
                'no_warnings': True,
                **get_platform_config(video_obj.platform)
            }
            
            with yt_dlp.YoutubeDL(info_opts) as ydl:
                info = ydl.extract_info(video_obj.url, download=False)
                video_obj.title = info.get('title', 'Unknown')
                
                # Check if it has video formats
                formats = info.get('formats', [])
                video_formats = [f for f in formats if f.get('vcodec') != 'none']
                
                # If no video formats, try to get image/thumbnail
                if not video_formats:
                    # Look for high quality images/thumbnails
                    thumbnails = info.get('thumbnails', [])
                    
                    # Try to find the best quality image
                    best_thumb = None
                    for thumb in thumbnails:
                        if thumb.get('url'):
                            # Prefer larger images
                            if not best_thumb or (thumb.get('width', 0) * thumb.get('height', 0)) > (best_thumb.get('width', 0) * best_thumb.get('height', 0)):
                                best_thumb = thumb
                    
                    # If we found a good thumbnail/image, download it
                    if best_thumb and best_thumb.get('url'):
                        success = download_image_from_url(video_obj, best_thumb['url'], video_obj.title)
                        if success:
                            return video_obj
                    
                    # Try direct image extraction for Pinterest and other image platforms
                    if video_obj.platform in ['pinterest', 'instagram']:
                        image_url = info.get('url') or info.get('webpage_url')
                        if image_url:
                            # For Pinterest, try to extract direct image URL
                            if 'pinterest' in image_url or 'pin.it' in image_url:
                                try:
                                    # Pinterest specific image extraction
                                    import re
                                    
                                    # Look for Pinterest image URLs in the info
                                    info_str = str(info)
                                    
                                    # Find pinimg.com URLs (Pinterest CDN)
                                    pinimg_urls = re.findall(r'https://[^"\s]+\.pinimg\.com/[^"\s]+', info_str)
                                    for img_url in pinimg_urls:
                                        # Try different sizes: original (236x), 474x, 736x, etc.
                                        if any(size in img_url for size in ['236x', '474x', '736x', '1200x', 'originals']):
                                            if ('jpg' in img_url or 'png' in img_url or 'webp' in img_url):
                                                success = download_image_from_url(video_obj, img_url, video_obj.title)
                                                if success:
                                                    return video_obj
                                    
                                    # Try to find image URLs in different formats
                                    image_patterns = [
                                        r'https://[^"\s]+\.(jpg|jpeg|png|webp)',
                                        r'"(https://[^"]+pinimg\.com[^"]+)"',
                                        r'"url":\s*"([^"]+\.(jpg|jpeg|png|webp)[^"]*?)"'
                                    ]
                                    
                                    for pattern in image_patterns:
                                        matches = re.findall(pattern, info_str, re.IGNORECASE)
                                        for match in matches:
                                            img_url = match[0] if isinstance(match, tuple) else match
                                            if 'pinimg.com' in img_url or 'pinterest' in img_url:
                                                success = download_image_from_url(video_obj, img_url, video_obj.title)
                                                if success:
                                                    return video_obj
                                    
                                    # Also try thumbnail URLs from info
                                    if info.get('thumbnail'):
                                        success = download_image_from_url(video_obj, info['thumbnail'], video_obj.title)
                                        if success:
                                            return video_obj
                                            
                                except Exception as e:
                                    pass
                    
                    # If no image found, return error
                    video_obj.status = 'failed'
                    video_obj.error_message = f'Bu {video_obj.platform.title()} postdan video yoki rasm topilmadi. URL ni tekshiring.'
                    video_obj.save()
                    return video_obj
                    
        except Exception as e:
            # If info extraction fails, continue with regular download attempt
            pass
        
        # Create media directory if it doesn't exist
        media_path = os.path.join(settings.MEDIA_ROOT, 'downloads', video_obj.platform)
        os.makedirs(media_path, exist_ok=True)
        
        # Get platform-specific configuration
        platform_config = get_platform_config(video_obj.platform)
        
        # Try different format options in order of preference
        format_options = [
            'best[height<=720]/best',  # Prefer 720p or lower, fallback to best
            'best[height<=1080]/best',  # Prefer 1080p or lower, fallback to best
            'best',  # Just best available
            'worst',  # Last resort
        ]
        
        download_success = False
        last_error = None
        
        for format_selector in format_options:
            try:
                # Configure yt-dlp options
                ydl_opts = {
                    'outtmpl': os.path.join(media_path, '%(title)s.%(ext)s'),
                    'format': format_selector,
                    **platform_config
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    # Get video info first (only on first attempt)
                    if not video_obj.title or video_obj.title == 'Unknown':
                        info = ydl.extract_info(video_obj.url, download=False)
                        video_obj.title = info.get('title', 'Unknown')
                        video_obj.save()
                    else:
                        info = ydl.extract_info(video_obj.url, download=False)
                    
                    # Download the video
                    ydl.download([video_obj.url])
                    
                    # Find the downloaded file
                    expected_filename = ydl.prepare_filename(info)
                    if os.path.exists(expected_filename):
                        video_obj.filename = os.path.basename(expected_filename)
                        video_obj.file_path = expected_filename
                        video_obj.media_type = 'video'
                        video_obj.status = 'completed'
                        video_obj.completed_at = timezone.now()
                        video_obj.save()
                        
                        # Schedule automatic deletion after 10 minutes
                        try:
                            from .tasks import schedule_cleanup_after_download
                            schedule_cleanup_after_download(video_obj.id, delay_minutes=10)
                        except ImportError:
                            # If Celery is not available, use simple threading approach
                            import threading
                            import time
                            
                            def delayed_cleanup():
                                time.sleep(10 * 60)  # Wait 10 minutes
                                try:
                                    if os.path.exists(expected_filename):
                                        os.remove(expected_filename)
                                        video_obj.file_path = ''
                                        video_obj.filename = ''
                                        video_obj.save()
                                except Exception as e:
                                    pass  # Silently ignore cleanup errors
                            
                            cleanup_thread = threading.Thread(target=delayed_cleanup, daemon=True)
                            cleanup_thread.start()
                        
                        download_success = True
                        break
                    
            except Exception as e:
                last_error = str(e)
                # Continue to next format option
                continue
        
        if not download_success:
            video_obj.status = 'failed'
            # Provide user-friendly error messages
            if video_obj.platform == 'pinterest' and ('No video formats found' in str(last_error) or 'video formats' in str(last_error).lower()):
                video_obj.error_message = 'Bu Pinterest post videosiz. Faqat video bor postlarni yuklab olish mumkin.'
            elif video_obj.platform == 'instagram' and ('login' in str(last_error).lower() or 'private' in str(last_error).lower() or 'not available' in str(last_error).lower()):
                # Try bypass methods specifically designed for hosting
                try:
                    from .instagram_bypass import download_instagram_content_bypass
                    bypass_success, bypass_message = download_instagram_content_bypass(video_obj)
                    if bypass_success:
                        return video_obj
                except ImportError:
                    pass
                    
                # Try alternative Instagram extraction methods as fallback
                try:
                    alternative_success = _try_alternative_instagram_download(video_obj)
                    if alternative_success:
                        return video_obj
                except Exception:
                    pass
                video_obj.error_message = 'Bu Instagram post maxfiy, mavjud emas yoki server tomonidan bloklangan. Ochiq postlarni tanlang yoki keyinroq urinib ko\'ring.'
            elif video_obj.platform == 'facebook' and ('login' in str(last_error).lower() or 'private' in str(last_error).lower()):
                video_obj.error_message = 'Bu Facebook video maxfiy yoki mavjud emas. Ochiq videolarni tanlang.'
            elif video_obj.platform == 'tiktok' and 'video' in str(last_error).lower():
                video_obj.error_message = 'TikTok videosini yuklab olishda xatolik. URL ni tekshiring.'
            else:
                video_obj.error_message = f'Yuklab olish muvaffaqiyatsiz tugadi. Xatolik: {last_error}'
                
    except Exception as e:
        video_obj.status = 'failed'
        video_obj.error_message = f'Download failed: {str(e)}'
    
    video_obj.save()
    return video_obj


def download_instagram_video(video_obj):
    """
    Download Instagram video using the universal downloader (for backward compatibility)
    """
    # Set platform if not already set
    if not video_obj.platform or video_obj.platform == 'other':
        video_obj.platform = 'instagram'
        video_obj.save()
    
    return download_video(video_obj)


def get_available_formats(url):
    """
    Get available formats for a video URL (for debugging)
    """
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'listformats': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            },
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            return {
                'formats': [
                    {
                        'format_id': f.get('format_id', 'unknown'),
                        'ext': f.get('ext', 'unknown'),
                        'resolution': f.get('resolution', 'unknown'),
                        'filesize': f.get('filesize', 0),
                    }
                    for f in formats
                ],
                'format_count': len(formats)
            }
    except Exception as e:
        return {'error': str(e)}


def _try_alternative_instagram_download(video_obj):
    """
    Try multiple alternative methods to download Instagram content when main method fails
    Enhanced for hosting environments with multiple fallback strategies
    """
    import time
    import random
    from django.conf import settings
    
    try:
        # Wait to avoid rate limiting
        time.sleep(random.uniform(2, 5))
        
        media_path = os.path.join(settings.MEDIA_ROOT, 'downloads', video_obj.platform)
        os.makedirs(media_path, exist_ok=True)
        
        # Strategy 1: Try with Instagram mobile app user agents
        mobile_configs = [
            {
                'http_headers': {
                    'User-Agent': 'Instagram 302.0.0.23.109 Android (33/13; 420dpi; 1080x2400; samsung; SM-G991B; o1s; qcom; en_US; 511558019)',
                    'X-Instagram-AJAX': '1',
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': '*/*',
                    'Accept-Language': 'en-US,en;q=0.9'
                },
                'extractor_args': {'instagram': {'variant': 'mobile', 'api_version': 'v1'}},
                'format': 'worst[height<=360]/worst'  # Very low quality for hosting
            },
            {
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Linux; Android 12; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Mobile Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Referer': 'https://www.instagram.com/'
                },
                'format': 'best[height<=480]/worst'
            }
        ]
        
        # Strategy 2: Try with different format selectors
        format_strategies = [
            'worst[ext=mp4]',
            'worst',
            'best[height<=240]',
            'best[height<=360]',
            'best[filesize<=10M]'
        ]
        
        # Try each mobile config
        for i, config in enumerate(mobile_configs):
            try:
                base_opts = {
                    'outtmpl': os.path.join(media_path, '%(title)s.%(ext)s'),
                    'quiet': True,
                    'no_warnings': True,
                    'socket_timeout': 90,  # Longer timeout for hosting
                    'retries': 8,
                    'fragment_retries': 15,
                    'skip_unavailable_fragments': True,
                    'geo_bypass': True,
                    'geo_bypass_country': 'US',
                    'prefer_ipv4': True,
                    'sleep_interval': 4,
                    'max_sleep_interval': 8,
                    **config
                }
                
                # Try different formats with this config
                for format_sel in format_strategies[:2]:  # Limit attempts
                    try:
                        ydl_opts = {**base_opts, 'format': format_sel}
                        
                        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                            info = ydl.extract_info(video_obj.url, download=False)
                            video_obj.title = info.get('title', 'Instagram Video')
                            
                            # Try to download
                            ydl.download([video_obj.url])
                            
                            # Find the downloaded file
                            expected_filename = ydl.prepare_filename(info)
                            if os.path.exists(expected_filename):
                                video_obj.filename = os.path.basename(expected_filename)
                                video_obj.file_path = expected_filename
                                video_obj.media_type = 'video'
                                video_obj.status = 'completed'
                                video_obj.completed_at = timezone.now()
                                video_obj.save()
                                return True
                                
                        # Wait between format attempts
                        time.sleep(random.uniform(3, 6))
                        
                    except Exception as e:
                        continue
                
                # Wait between config attempts
                time.sleep(random.uniform(5, 8))
                
            except Exception as e:
                continue
        
        # Strategy 3: Try image extraction if video fails
        try:
            info_opts = {
                'quiet': True,
                'no_warnings': True,
                'http_headers': _get_random_instagram_headers(),
                'socket_timeout': 60,
                'prefer_ipv4': True,
                'geo_bypass': True
            }
            
            with yt_dlp.YoutubeDL(info_opts) as ydl:
                info = ydl.extract_info(video_obj.url, download=False)
                
                # Look for thumbnails/images
                thumbnails = info.get('thumbnails', [])
                if thumbnails:
                    # Get the best quality thumbnail
                    best_thumb = max(thumbnails, key=lambda x: x.get('width', 0) * x.get('height', 0))
                    if best_thumb.get('url'):
                        success = download_image_from_url(video_obj, best_thumb['url'], info.get('title', 'Instagram Image'))
                        if success:
                            return True
        except Exception:
            pass
                
        return False
        
    except Exception as e:
        return False


def get_video_info(url):
    """
    Get video information without downloading
    """
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'format': 'best',
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            },
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                'title': info.get('title', 'Unknown'),
                'duration': info.get('duration', 0),
                'view_count': info.get('view_count', 0),
                'uploader': info.get('uploader', 'Unknown'),
                'description': info.get('description', ''),
                'thumbnail': info.get('thumbnail', ''),
                'formats': len(info.get('formats', [])) if info.get('formats') else 0,
            }
    except Exception as e:
        return {'error': str(e)}
