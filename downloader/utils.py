import os
import re
import yt_dlp
from django.conf import settings
from django.utils import timezone
from .models import DownloadedVideo


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
        r'(?:https?://)?(?:www\.)?pinterest\.[^/]+/.*'
    ]
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
    }
    
    platform_configs = {
        'instagram': {
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            },
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
        
        # Platform-specific pre-checks
        if video_obj.platform == 'pinterest':
            # Pinterest often contains images, not videos
            try:
                # Quick check to see if this URL actually contains video
                test_opts = {'quiet': True, 'no_warnings': True, 'simulate': True}
                with yt_dlp.YoutubeDL(test_opts) as ydl:
                    info = ydl.extract_info(video_obj.url, download=False)
                    formats = info.get('formats', [])
                    if not formats:
                        video_obj.status = 'failed'
                        video_obj.error_message = 'Bu Pinterest post videosiz, faqat rasm bor. Video yuklab olish uchun video bor postni tanlang.'
                        video_obj.save()
                        return video_obj
            except Exception as e:
                if 'No video formats found' in str(e):
                    video_obj.status = 'failed'
                    video_obj.error_message = 'Bu Pinterest post videosiz. Faqat video bor postlarni yuklab olish mumkin.'
                    video_obj.save()
                    return video_obj
        
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
                        video_obj.status = 'completed'
                        video_obj.completed_at = timezone.now()
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
            elif video_obj.platform == 'instagram' and 'login' in str(last_error).lower():
                video_obj.error_message = 'Bu Instagram post maxfiy yoki mavjud emas. Ochiq postlarni tanlang.'
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
