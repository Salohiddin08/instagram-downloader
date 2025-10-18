from celery import shared_task
from django.core.management import call_command
from django.utils import timezone
from datetime import timedelta
import os
import logging
from .models import DownloadedVideo

logger = logging.getLogger(__name__)

@shared_task
def cleanup_old_files(minutes=10):
    """
    Celery task to clean up files older than specified minutes
    """
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
                
                os.remove(download.file_path)
                
                # Clear file path in database
                download.file_path = ''
                download.filename = ''
                download.save()
                
                deleted_count += 1
                freed_space += file_size
                
                logger.info(
                    f"Deleted file: {download.filename} "
                    f"({file_size / (1024*1024):.2f} MB) "
                    f"from {download.platform}"
                )
                
            except OSError as e:
                logger.error(f"Error deleting file {download.file_path}: {e}")
    
    logger.info(
        f"Cleanup task completed: Deleted {deleted_count} files, "
        f"freed {freed_space / (1024*1024):.2f} MB"
    )
    
    return {
        'deleted_count': deleted_count,
        'freed_space_mb': freed_space / (1024*1024)
    }


def schedule_cleanup_after_download(download_id, delay_minutes=10):
    """
    Schedule cleanup for a specific download after delay
    """
    cleanup_specific_file.apply_async(
        args=[download_id],
        countdown=delay_minutes * 60  # Convert to seconds
    )


@shared_task
def cleanup_specific_file(download_id):
    """
    Clean up a specific downloaded file
    """
    try:
        download = DownloadedVideo.objects.get(id=download_id)
        
        if download.file_path and os.path.exists(download.file_path):
            file_size = os.path.getsize(download.file_path)
            os.remove(download.file_path)
            
            # Clear file path in database
            download.file_path = ''
            download.filename = ''
            download.save()
            
            logger.info(
                f"Auto-deleted file: {download.filename} "
                f"({file_size / (1024*1024):.2f} MB) "
                f"from {download.platform} after 10 minutes"
            )
            
            return True
            
    except DownloadedVideo.DoesNotExist:
        logger.warning(f"Download with ID {download_id} not found for cleanup")
    except Exception as e:
        logger.error(f"Error in cleanup_specific_file: {e}")
    
    return False