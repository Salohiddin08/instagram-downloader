#!/bin/bash
# Automatic file cleanup script
# Add this to your crontab: */5 * * * * /path/to/cleanup_cron.sh

cd /home/salohiddin/downlaoderf/instagram-downloader

# Activate virtual environment
source /home/salohiddin/downlaoderf/venv/bin/activate

# Run cleanup command (delete files older than 10 minutes)
python manage.py cleanup_files --minutes 10

# Optional: Run cleanup every 5 minutes with different retention
# python manage.py cleanup_files --minutes 15

echo "Cleanup completed at $(date)" >> /tmp/cleanup.log