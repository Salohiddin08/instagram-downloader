from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('status/<int:pk>/', views.download_status, name='download_status'),
    path('list/', views.download_list, name='download_list'),
    path('download/<int:pk>/', views.download_file, name='download_file'),
    path('api/status/<int:pk>/', views.check_status, name='check_status'),
    path('api/preview/', views.preview_video, name='preview_video'),
    # Authentication URLs
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('signup/', views.SignUpView.as_view(), name='signup'),
    # Telegram Authentication URLs
    path('telegram-login/', views.telegram_login, name='telegram_login'),
    path('telegram-verify-otp/', views.telegram_verify_otp, name='telegram_verify_otp'),
    path('telegram-resend-otp/', views.telegram_resend_otp, name='telegram_resend_otp'),
    path('telegram-link/', views.telegram_link_account, name='telegram_link_account'),
    path('telegram-verify-link/', views.telegram_verify_link, name='telegram_verify_link'),
]
