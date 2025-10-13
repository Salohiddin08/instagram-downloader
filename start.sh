#!/bin/bash

echo "🚀 Starting Instagram Video Downloader..."

# Activate virtual environment
source venv/bin/activate

# Check if migrations are needed
echo "📦 Checking database migrations..."
python manage.py makemigrations --dry-run --verbosity=0 >/dev/null 2>&1
if [ $? -eq 0 ]; then
    python manage.py makemigrations
    python manage.py migrate
fi

# Create media directory if it doesn't exist
mkdir -p media/downloads

echo "✅ Setup complete!"
echo ""
echo "🌐 Starting Django development server..."
echo "📱 Open your browser and go to: http://127.0.0.1:8000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the development server
python manage.py runserver