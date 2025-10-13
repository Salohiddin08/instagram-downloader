from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('status/<int:pk>/', views.download_status, name='download_status'),
    path('list/', views.download_list, name='download_list'),
    path('download/<int:pk>/', views.download_file, name='download_file'),
    path('api/status/<int:pk>/', views.check_status, name='check_status'),
    path('api/preview/', views.preview_video, name='preview_video'),
]