from django.contrib import admin
from .models import DownloadedVideo


@admin.register(DownloadedVideo)
class DownloadedVideoAdmin(admin.ModelAdmin):
    list_display = ['title', 'url', 'status', 'created_at', 'completed_at']
    list_filter = ['status', 'created_at']
    search_fields = ['title', 'url']
    readonly_fields = ['created_at', 'completed_at']
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ['url']
        return self.readonly_fields
