from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
import random
import string


class DownloadedVideo(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('downloading', 'Downloading'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    PLATFORM_CHOICES = [
        ('instagram', 'Instagram'),
        ('facebook', 'Facebook'),
        ('tiktok', 'TikTok'),
        ('pinterest', 'Pinterest'),
        ('other', 'Other'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    url = models.URLField(max_length=500)
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES, default='other')
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


class TelegramUser(models.Model):
    """Model to store Telegram user information"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='telegram_profile')
    telegram_id = models.BigIntegerField(unique=True)
    username = models.CharField(max_length=255, blank=True, null=True)
    first_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    is_verified = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.telegram_id}"


class TelegramOTP(models.Model):
    """Model to store OTP codes for Telegram authentication"""
    phone_number = models.CharField(max_length=20, db_index=True)
    telegram_id = models.BigIntegerField(null=True, blank=True, db_index=True)
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)
    max_attempts = models.IntegerField(default=3)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.phone_number} - {self.otp_code}"
    
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    def is_valid(self):
        return not self.is_used and not self.is_expired() and self.attempts < self.max_attempts
    
    @classmethod
    def generate_otp(cls):
        """Generate a 6-digit OTP code"""
        return ''.join(random.choices(string.digits, k=6))
    
    def save(self, *args, **kwargs):
        if not self.otp_code:
            self.otp_code = self.generate_otp()
        if not self.expires_at:
            # OTP expires in 10 minutes
            self.expires_at = timezone.now() + timezone.timedelta(minutes=10)
        super().save(*args, **kwargs)
