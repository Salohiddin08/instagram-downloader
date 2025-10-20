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
        r'(?:https?://)?fb\.watch/([A-Za-z0-9_-]+)/?'
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
    """
    import random
    
    user_agents = [
        'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Mobile/15E148 Safari/604.1',
        'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1',
        'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Mobile Safari/537.36',
        'Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.91 Mobile Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15'
    ]
    
    return {
        'User-Agent': random.choice(user_agents),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
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
    """
    base_config = {
        'writeinfojson': False,
        'writesubtitles': False,
        'writeautomaticsub': False,
        'no_warnings': True,
        'ignoreerrors': False,
        'extractaudio': False,
        # Add timeout settings for production
        'socket_timeout': 30,
        'retries': 3,
        # Force IPv4 for PythonAnywhere compatibility
        'prefer_ipv4': True,
        # Add geo-bypass for restricted content
        'geo_bypass': True,
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
            # Add more options for Instagram
            'sleep_interval': 1,
            'max_sleep_interval': 3,
            'extractor_args': {
                'instagram': {
                    'api_version': 'v1',
                    'include_stories': False
                }
            }
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
                # Try alternative Instagram extraction methods
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
    Try alternative methods to download Instagram content when main method fails
    """
    try:
        import time
        
        # Wait a bit to avoid rate limiting
        time.sleep(2)
        
        # Try with different user agents and configurations
        alternative_configs = [
            {
                'http_headers': {
                    'User-Agent': 'Instagram 219.0.0.12.117 Android',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                'extractor_args': {'instagram': {'variant': 'mobile'}}
            },
            {
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Linux; Android 9; SM-G960F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.89 Mobile Safari/537.36'
                },
                'sleep_interval': 2,
                'max_sleep_interval': 5
            }
        ]
        
        media_path = os.path.join(settings.MEDIA_ROOT, 'downloads', video_obj.platform)
        os.makedirs(media_path, exist_ok=True)
        
        for config in alternative_configs:
            try:
                ydl_opts = {
                    'outtmpl': os.path.join(media_path, '%(title)s.%(ext)s'),
                    'format': 'best[height<=480]/worst',  # Use lower quality to avoid blocks
                    'quiet': True,
                    'no_warnings': True,
                    'socket_timeout': 45,
                    'retries': 5,
                    **config
                }
                
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
                        
                time.sleep(3)  # Wait between attempts
                        
            except Exception:
                continue
                
        return False
        
    except Exception:
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
