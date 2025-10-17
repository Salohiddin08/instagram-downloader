#!/bin/bash

BOT_TOKEN="8276877025:AAFFPx5w397Zris6iSzFCe4cs6yrcwnnx0E"

case "$1" in
    start)
        echo "🤖 Starting Enhanced Telegram Bot..."
        # Kill any existing bot processes first
        pkill -f "telegram_bot.py" 2>/dev/null
        pkill -f "enhanced_telegram" 2>/dev/null
        pkill -f "$BOT_TOKEN" 2>/dev/null
        
        # Wait for Telegram to clear conflicts
        sleep 3
        
        # Start the enhanced bot
        nohup python enhanced_telegram_bot.py $BOT_TOKEN > telegram_bot.log 2>&1 &
        echo "✅ Bot started! Check telegram_bot.log for details."
        ;;
    
    stop)
        echo "🛑 Stopping all Telegram bot processes..."
        pkill -f "telegram_bot.py" 2>/dev/null
        pkill -f "enhanced_telegram" 2>/dev/null
        pkill -f "$BOT_TOKEN" 2>/dev/null
        echo "✅ All bot processes stopped."
        ;;
    
    restart)
        echo "🔄 Restarting bot..."
        $0 stop
        sleep 3
        $0 start
        ;;
    
    status)
        echo "📊 Checking bot status..."
        if pgrep -f "enhanced_telegram" > /dev/null; then
            echo "✅ Enhanced bot is running"
            echo "📋 Recent logs:"
            tail -n 5 telegram_bot.log 2>/dev/null || echo "No log file found"
        else
            echo "❌ No bot processes running"
        fi
        ;;
    
    log)
        echo "📜 Bot logs:"
        tail -f telegram_bot.log
        ;;
    
    *)
        echo "🤖 Telegram Bot Manager"
        echo "Usage: $0 {start|stop|restart|status|log}"
        echo ""
        echo "Commands:"
        echo "  start   - Start the enhanced telegram bot"
        echo "  stop    - Stop all telegram bot processes"
        echo "  restart - Restart the bot (stop + start)"
        echo "  status  - Check if bot is running"
        echo "  log     - Show bot logs in real-time"
        exit 1
        ;;
esac