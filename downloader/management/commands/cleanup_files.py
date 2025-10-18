from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import os
import logging
from downloader.models import DownloadedVideo

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Clean up downloaded files older than specified minutes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--minutes',
            type=int,
            default=10,
            help='Delete files older than this many minutes (default: 10)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )

    def handle(self, *args, **options):
        minutes = options['minutes']
        dry_run = options['dry_run']
        
        cutoff_time = timezone.now() - timedelta(minutes=minutes)
        
        # Find completed downloads older than cutoff time
        old_downloads = DownloadedVideo.objects.filter(
            status='completed',
            completed_at__lt=cutoff_time,
            file_path__isnull=False
        ).exclude(file_path='')
        
        deleted_count = 0
        freed_space = 0
        
        for download in old_downloads:
            if download.file_path and os.path.exists(download.file_path):
                try:
                    # Get file size before deletion
                    file_size = os.path.getsize(download.file_path)
                    
                    if dry_run:
                        self.stdout.write(
                            f"Would delete: {download.file_path} "
                            f"({file_size / (1024*1024):.2f} MB) "
                            f"from {download.platform} - {download.title[:30]}..."
                        )
                    else:
                        os.remove(download.file_path)
                        # Clear file path in database
                        download.file_path = ''
                        download.filename = ''
                        download.save()
                        
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"Deleted: {download.filename} "
                                f"({file_size / (1024*1024):.2f} MB) "
                                f"from {download.platform}"
                            )
                        )
                    
                    deleted_count += 1
                    freed_space += file_size
                    
                except OSError as e:
                    logger.error(f"Error deleting file {download.file_path}: {e}")
                    self.stdout.write(
                        self.style.ERROR(f"Failed to delete: {download.file_path}")
                    )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"DRY RUN: Would delete {deleted_count} files, "
                    f"freeing {freed_space / (1024*1024):.2f} MB"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Cleanup completed: Deleted {deleted_count} files, "
                    f"freed {freed_space / (1024*1024):.2f} MB"
                )
            )