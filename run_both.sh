#!/bin/bash

# Start Django development server in background
echo "Starting Django server..."
python manage.py runserver 0.0.0.0:8000 &
DJANGO_PID=$!

# Start Telegram bot
echo "Starting Telegram bot..."
python manage.py run_telegram_bot &
BOT_PID=$!

# Function to cleanup processes on exit
cleanup() {
    echo "Stopping services..."
    kill $DJANGO_PID 2>/dev/null
    kill $BOT_PID 2>/dev/null
    exit
}

# Trap signals to cleanup
trap cleanup SIGINT SIGTERM

echo "Both services started. Press Ctrl+C to stop both."
echo "Django server PID: $DJANGO_PID"
echo "Telegram bot PID: $BOT_PID"

# Wait for both processes
wait