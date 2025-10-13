from django.db import models
from django.utils import timezone


class DownloadedVideo(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('downloading', 'Downloading'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    url = models.URLField(max_length=500)
    title = models.CharField(max_length=255, blank=True)
    filename = models.CharField(max_length=255, blank=True)
    file_path = models.CharField(max_length=500, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title or self.url} - {self.status}"
