import os
import yt_dlp
from django.conf import settings
from django.utils import timezone
from .models import DownloadedVideo


def download_instagram_video(video_obj):
    """
    Download Instagram video using yt-dlp with multiple format fallbacks
    """
    try:
        # Update status to downloading
        video_obj.status = 'downloading'
        video_obj.save()
        
        # Create media directory if it doesn't exist
        media_path = os.path.join(settings.MEDIA_ROOT, 'downloads')
        os.makedirs(media_path, exist_ok=True)
        
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
                    'writeinfojson': False,
                    'writesubtitles': False,
                    'writeautomaticsub': False,
                    'no_warnings': True,
                    'ignoreerrors': False,
                    'extractaudio': False,
                    # Instagram-specific options
                    'http_headers': {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                    },
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
            video_obj.error_message = f'All format attempts failed. Last error: {last_error}'
                
    except Exception as e:
        video_obj.status = 'failed'
        video_obj.error_message = f'Download failed: {str(e)}'
    
    video_obj.save()
    return video_obj


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
