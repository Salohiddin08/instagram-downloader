# Instagram Video Downloader

A Django web application for downloading Instagram videos, reels, posts, and IGTV content using yt-dlp.

## Features

- Download Instagram posts, reels, stories, and IGTV videos
- Modern, responsive web interface
- Real-time download progress tracking
- Download history and management
- Automatic file organization
- Error handling and retry mechanisms

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Virtual environment (recommended)

## Installation

1. **Clone or navigate to the project directory:**
   ```bash
   cd instagram_downloader
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install required dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run database migrations:**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Create a superuser (optional):**
   ```bash
   python manage.py createsuperuser
   ```

6. **Start the development server:**
   ```bash
   python manage.py runserver
   ```

7. **Access the application:**
   Open your web browser and go to `http://127.0.0.1:8000`

## Usage

### Downloading Videos

1. **Get Instagram URL:**
   - Copy any Instagram post, reel, story, or IGTV URL
   - Examples:
     - Posts: `https://www.instagram.com/p/ABC123/`
     - Reels: `https://www.instagram.com/reel/ABC123/`
     - Stories: `https://www.instagram.com/stories/username/123456/`
     - IGTV: `https://www.instagram.com/tv/ABC123/`

2. **Start Download:**
   - Paste the URL in the input field on the home page
   - Click "Download" button
   - You'll be redirected to a status page

3. **Monitor Progress:**
   - The status page shows real-time download progress
   - Page automatically refreshes to show updates
   - Download button appears when complete

4. **Download File:**
   - Click the download button when the video is ready
   - Files are saved in the `media/downloads/` directory

### Managing Downloads

- **View All Downloads:** Click "Downloads" in the navigation
- **Check Status:** Click the info icon for any download
- **Download Files:** Click the download icon for completed videos

## Project Structure

```
instagram_downloader/
├── downloader/              # Django app for downloading functionality
│   ├── models.py           # Database models
│   ├── views.py            # View functions
│   ├── forms.py            # Form definitions
│   ├── utils.py            # Download utilities using yt-dlp
│   ├── urls.py             # URL routing
│   └── templates/          # HTML templates
├── instagram_project/       # Django project settings
│   ├── settings.py         # Project configuration
│   └── urls.py             # Main URL routing
├── media/                   # Downloaded files storage
├── manage.py               # Django management script
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Technical Details

### Dependencies

- **Django 5.2.7:** Web framework
- **yt-dlp:** YouTube/Instagram video downloader library
- **requests:** HTTP library for API calls

### Features

- **Asynchronous Downloads:** Downloads run in background threads
- **Real-time Updates:** AJAX-based status checking
- **Error Handling:** Comprehensive error catching and reporting
- **Responsive Design:** Mobile-friendly Bootstrap interface
- **File Management:** Automatic file organization and cleanup

### Database Models

- **DownloadedVideo:** Tracks download requests and status
  - URL, title, filename, status, timestamps
  - Error messages and file paths

## Configuration

### Django Settings

Key settings in `instagram_project/settings.py`:

```python
# Media files configuration
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Add downloader app
INSTALLED_APPS = [
    # ... other apps
    'downloader',
]
```

### yt-dlp Configuration

Download settings in `downloader/utils.py`:

```python
ydl_opts = {
    'outtmpl': 'media/downloads/%(title)s.%(ext)s',
    'format': 'best[height<=720]',  # Max 720p quality
}
```

## Troubleshooting

### Common Issues

1. **"No module named" errors:**
   - Ensure virtual environment is activated
   - Run `pip install -r requirements.txt`

2. **Download failures:**
   - Check Instagram URL format
   - Ensure stable internet connection
   - Instagram may block automated requests temporarily

3. **File not found errors:**
   - Check media directory permissions
   - Ensure sufficient disk space

4. **Port already in use:**
   - Use different port: `python manage.py runserver 8001`

### Debug Mode

For development, debug mode is enabled by default. For production:

1. Set `DEBUG = False` in settings.py
2. Configure `ALLOWED_HOSTS`
3. Use a production WSGI server

## Legal Notice

This tool is for personal use and educational purposes only. Please respect Instagram's Terms of Service and copyright laws. Only download content you have permission to download.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is for educational purposes. Please review Instagram's terms of service before using.# instagram-downloader
# instagram-downloader
# instagram-downloader
# instagram-downloader
# instagram-downloader
# instagram-downloader
# instagram-downloader
