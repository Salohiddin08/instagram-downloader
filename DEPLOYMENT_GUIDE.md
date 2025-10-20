# PythonAnywhere Deployment Guide

## Issues and Solutions

### 1. Telegram Authentication Not Working

**Problem:** The Telegram bot can't send OTP messages due to async/await issues in production.

**Solution:**
1. Update `telegram_utils.py` to use synchronous HTTP requests instead of async Telegram bot
2. Use direct Telegram Bot API calls with `requests` library

### 2. Video Downloads Failing

**Problem:** yt-dlp might have issues with external requests on PythonAnywhere free accounts.

**Solutions:**
1. Added timeout and retry settings in `get_platform_config()`
2. Added IPv4 preference for better compatibility
3. Created proper logging to debug issues

### 3. Static Files and Media Setup

**Problem:** Static files and media directories not properly configured for production.

**Solution:** Updated settings.py with proper STATIC_ROOT and media directory creation.

## Deployment Steps

### 1. Environment Variables
Set these environment variables in PythonAnywhere:
```bash
DEBUG=False
TELEGRAM_BOT_TOKEN=8276877025:AAFFPx5w397Zris6iSzFCe4cs6yrcwnnx0E
TELEGRAM_BOT_USERNAME=social_downloader_site_bot
```

### 2. Static Files
Run collectstatic in PythonAnywhere console:
```bash
cd /home/yourusername/mysite
python manage.py collectstatic --noinput
```

### 3. Database Migration
Run migrations:
```bash
python manage.py migrate
```

### 4. Media Directories
Ensure media directories have proper permissions:
```bash
mkdir -p media/downloads/{instagram,facebook,tiktok,pinterest}
chmod 755 media/downloads/
```

### 5. Telegram Bot Setup

For the Telegram bot to work, you need to:

1. **Run the bot on PythonAnywhere Tasks (if available) or Always-On Tasks:**
   ```bash
   cd /home/yourusername/mysite
   python working_bot.py
   ```

2. **Or use webhook instead of polling (recommended for production):**
   - Set up webhook endpoint in your Django views
   - Configure webhook URL with Telegram

## Alternative Telegram Fix

If async issues persist, replace the async Telegram bot code with direct HTTP requests:

```python
import requests

def send_telegram_message(chat_id, message, bot_token):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'HTML'
    }
    response = requests.post(url, data=data, timeout=30)
    return response.status_code == 200
```

## Debugging Tips

1. **Check error logs in PythonAnywhere console:**
   ```bash
   tail -f /var/log/yourusername.pythonanywhere.com.error.log
   ```

2. **Enable Django debug logging by setting DEBUG=True temporarily**

3. **Test individual components:**
   - Test video download: `python manage.py shell` → import utils and test download_video
   - Test Telegram: Create a simple test script to send messages

## Common PythonAnywhere Limitations

1. **Free accounts can't use external libraries that require compilation**
2. **Limited outbound internet requests**
3. **No persistent background processes on free accounts**
4. **Some social media sites may block PythonAnywhere IPs**

## Recommended Production Setup

1. **Use webhook for Telegram bot instead of polling**
2. **Implement proper error handling and logging**
3. **Consider upgrading to paid PythonAnywhere account for better external access**
4. **Use Redis for task queuing if available**