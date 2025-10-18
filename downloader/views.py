from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.http import JsonResponse, FileResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.generic import ListView, CreateView
from django.urls import reverse_lazy
import os
import threading

from .models import DownloadedVideo, TelegramOTP, TelegramUser
from .forms import VideoDownloadForm, CustomUserCreationForm
from .utils import download_video, get_video_info, detect_platform
from .telegram_utils import telegram_service


@login_required
def home(request):
    """Home page with download form"""
    if request.method == 'POST':
        form = VideoDownloadForm(request.POST)
        if form.is_valid():
            video = form.save(commit=False)
            video.user = request.user
            
            # Detect and set platform
            platform = detect_platform(video.url)
            video.platform = platform
            video.save()
            
            # Start download in background thread
            thread = threading.Thread(target=download_video, args=(video,))
            thread.daemon = True
            thread.start()
            
            messages.success(request, f'Download started for: {video.url}')
            return redirect('download_status', pk=video.pk)
    else:
        form = VideoDownloadForm()
    
    # Show only user's recent downloads
    recent_downloads = DownloadedVideo.objects.filter(user=request.user)[:5]
    return render(request, 'downloader/home.html', {
        'form': form,
        'recent_downloads': recent_downloads
    })


@login_required
def download_status(request, pk):
    """Show download status page"""
    video = get_object_or_404(DownloadedVideo, pk=pk, user=request.user)
    return render(request, 'downloader/status.html', {'video': video})


@login_required
def download_list(request):
    """List all downloads for the current user"""
    downloads = DownloadedVideo.objects.filter(user=request.user)
    return render(request, 'downloader/list.html', {'downloads': downloads})


@login_required
def download_file(request, pk):
    """Download completed file"""
    video = get_object_or_404(DownloadedVideo, pk=pk, user=request.user)
    
    if video.status != 'completed' or not video.file_path:
        raise Http404("File not available")
    
    if not os.path.exists(video.file_path):
        raise Http404("File not found")
    
    return FileResponse(
        open(video.file_path, 'rb'),
        as_attachment=True,
        filename=video.filename
    )


@login_required
@csrf_exempt
def check_status(request, pk):
    """AJAX endpoint to check download status"""
    video = get_object_or_404(DownloadedVideo, pk=pk, user=request.user)
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


class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    redirect_authenticated_user = True
    success_url = reverse_lazy('home')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Login'
        return context


def logout_view(request):
    """Custom logout view that logs out user and redirects to home"""
    from django.contrib.auth import logout
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('login')


class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'registration/signup.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Sign Up'
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        username = form.cleaned_data.get('username')
        messages.success(self.request, f'Account created for {username}! You can now log in.')
        return response


# Telegram Authentication Views
def telegram_login(request):
    """Initiate Telegram login process using phone number"""
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number', '').strip()
        
        if not phone_number:
            messages.error(request, 'Please enter your phone number')
            return render(request, 'registration/telegram_login.html')
        
        # Normalize phone number format
        if not phone_number.startswith('+'):
            phone_number = '+' + phone_number
        
        # Create and send OTP
        otp, error_message = telegram_service.create_otp_for_phone_number(phone_number)
        
        if otp:
            # Store phone_number in session for OTP verification
            request.session['phone_number'] = phone_number
            messages.success(request, 'OTP code has been sent to your Telegram account!')
            return redirect('telegram_verify_otp')
        else:
            messages.error(request, error_message or 'Failed to send OTP. Please make sure you have registered with our bot.')
    
    return render(request, 'registration/telegram_login.html')


def telegram_verify_otp(request):
    """Verify OTP and complete Telegram login"""
    phone_number = request.session.get('phone_number')
    
    if not phone_number:
        messages.error(request, 'Please start the login process again')
        return redirect('telegram_login')
    
    if request.method == 'POST':
        otp_code = request.POST.get('otp_code', '').strip()
        
        if not otp_code:
            messages.error(request, 'Please enter the OTP code')
            return render(request, 'registration/telegram_verify_otp.html', {'phone_number': phone_number})
        
        # Verify OTP
        is_valid, message = telegram_service.verify_otp(phone_number, otp_code)
        
        if is_valid:
            # OTP is valid, now get or create user account
            user, user_message = telegram_service.get_or_create_user_from_phone(phone_number)
            
            if user:
                # Log the user in with explicit backend
                from django.contrib.auth import login as auth_login
                # Set backend attribute as backup
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                # Clear session data
                if 'phone_number' in request.session:
                    del request.session['phone_number']
                
                messages.success(request, f'Successfully logged in via Telegram! {user_message}')
                return redirect('home')
            else:
                messages.error(request, f'Failed to create user account: {user_message}')
        else:
            messages.error(request, message)
    
    return render(request, 'registration/telegram_verify_otp.html', {'phone_number': phone_number})


def telegram_resend_otp(request):
    """Resend OTP code to Telegram"""
    phone_number = request.session.get('phone_number')
    
    if not phone_number:
        messages.error(request, 'Please start the login process again')
        return redirect('telegram_login')
    
    # Create and send new OTP
    otp, error_message = telegram_service.create_otp_for_phone_number(phone_number)
    
    if otp:
        messages.success(request, 'New OTP code has been sent to your Telegram account!')
    else:
        messages.error(request, error_message or 'Failed to send OTP. Please try again.')
    
    return redirect('telegram_verify_otp')


@login_required
def telegram_link_account(request):
    """Link existing account with Telegram"""
    if hasattr(request.user, 'telegram_profile'):
        messages.info(request, 'Your account is already linked to Telegram')
        return redirect('home')
    
    if request.method == 'POST':
        telegram_id = request.POST.get('telegram_id', '').strip()
        
        if not telegram_id:
            messages.error(request, 'Please enter your Telegram ID')
            return render(request, 'registration/telegram_link.html')
        
        try:
            telegram_id = int(telegram_id)
        except ValueError:
            messages.error(request, 'Invalid Telegram ID format')
            return render(request, 'registration/telegram_link.html')
        
        # Check if this Telegram ID is already linked to another account
        if TelegramUser.objects.filter(telegram_id=telegram_id).exists():
            messages.error(request, 'This Telegram account is already linked to another user')
            return render(request, 'registration/telegram_link.html')
        
        # Create and send OTP for verification
        otp = telegram_service.create_otp_for_telegram_id(telegram_id)
        
        if otp:
            request.session['link_telegram_id'] = telegram_id
            messages.success(request, 'OTP code has been sent to your Telegram account!')
            return redirect('telegram_verify_link')
        else:
            messages.error(request, 'Failed to send OTP. Please make sure your Telegram ID is correct and you have started the bot.')
    
    return render(request, 'registration/telegram_link.html')


@login_required
def telegram_verify_link(request):
    """Verify OTP and link account to Telegram"""
    telegram_id = request.session.get('link_telegram_id')
    
    if not telegram_id:
        messages.error(request, 'Please start the linking process again')
        return redirect('telegram_link_account')
    
    if request.method == 'POST':
        otp_code = request.POST.get('otp_code', '').strip()
        
        if not otp_code:
            messages.error(request, 'Please enter the OTP code')
            return render(request, 'registration/telegram_verify_link.html', {'telegram_id': telegram_id})
        
        # Verify OTP
        is_valid, message = telegram_service.verify_otp(telegram_id, otp_code)
        
        if is_valid:
            # Create Telegram user profile
            TelegramUser.objects.create(
                user=request.user,
                telegram_id=telegram_id,
                is_verified=True
            )
            
            # Clear session data
            if 'link_telegram_id' in request.session:
                del request.session['link_telegram_id']
            
            messages.success(request, 'Your account has been successfully linked to Telegram!')
            return redirect('home')
        else:
            messages.error(request, message)
    
    return render(request, 'registration/telegram_verify_link.html', {'telegram_id': telegram_id})
