from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse, FileResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.generic import ListView
import os
import threading

from .models import DownloadedVideo
from .forms import VideoDownloadForm
from .utils import download_instagram_video, get_video_info


def home(request):
    """Home page with download form"""
    if request.method == 'POST':
        form = VideoDownloadForm(request.POST)
        if form.is_valid():
            video = form.save()
            # Start download in background thread
            thread = threading.Thread(target=download_instagram_video, args=(video,))
            thread.daemon = True
            thread.start()
            
            messages.success(request, f'Download started for: {video.url}')
            return redirect('download_status', pk=video.pk)
    else:
        form = VideoDownloadForm()
    
    recent_downloads = DownloadedVideo.objects.all()[:5]
    return render(request, 'downloader/home.html', {
        'form': form,
        'recent_downloads': recent_downloads
    })


def download_status(request, pk):
    """Show download status page"""
    video = get_object_or_404(DownloadedVideo, pk=pk)
    return render(request, 'downloader/status.html', {'video': video})


def download_list(request):
    """List all downloads"""
    downloads = DownloadedVideo.objects.all()
    return render(request, 'downloader/list.html', {'downloads': downloads})


def download_file(request, pk):
    """Download completed file"""
    video = get_object_or_404(DownloadedVideo, pk=pk)
    
    if video.status != 'completed' or not video.file_path:
        raise Http404("File not available")
    
    if not os.path.exists(video.file_path):
        raise Http404("File not found")
    
    return FileResponse(
        open(video.file_path, 'rb'),
        as_attachment=True,
        filename=video.filename
    )


@csrf_exempt
def check_status(request, pk):
    """AJAX endpoint to check download status"""
    video = get_object_or_404(DownloadedVideo, pk=pk)
    return JsonResponse({
        'status': video.status,
        'title': video.title,
        'filename': video.filename,
        'error_message': video.error_message,
        'completed_at': video.completed_at.isoformat() if video.completed_at else None,
    })


@csrf_exempt
def preview_video(request):
    """AJAX endpoint to preview video info"""
    if request.method == 'POST':
        url = request.POST.get('url')
        if url:
            info = get_video_info(url)
            return JsonResponse(info)
    return JsonResponse({'error': 'Invalid request'})
