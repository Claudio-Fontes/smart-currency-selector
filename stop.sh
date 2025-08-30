#!/bin/bash

echo "🛑 Stopping Solana Hot Pools Dashboard..."

# Function to kill processes on specific ports
kill_port() {
    local port=$1
    local pids=$(lsof -ti:$port 2>/dev/null)
    if [ ! -z "$pids" ]; then
        echo "🔥 Stopping processes on port $port..."
        echo $pids | xargs kill -9 2>/dev/null
        sleep 1
        
        # Check if processes were killed
        local remaining=$(lsof -ti:$port 2>/dev/null)
        if [ -z "$remaining" ]; then
            echo "✅ Port $port is now free"
        else
            echo "⚠️  Some processes on port $port may still be running"
        fi
    else
        echo "ℹ️  No processes found on port $port"
    fi
}

# Kill processes on both ports
kill_port 3000
kill_port 8000

# Also kill by process name as backup
echo "🧹 Cleaning up by process name..."
pkill -f "python3 backend/server.py" 2>/dev/null && echo "🔥 Killed Python backend" || echo "ℹ️  No Python backend found"
pkill -f "webpack-dev-server" 2>/dev/null && echo "🔥 Killed Webpack server" || echo "ℹ️  No Webpack server found"
pkill -f "npm run dev" 2>/dev/null && echo "🔥 Killed npm dev server" || echo "ℹ️  No npm dev server found"

# Final verification
sleep 1
echo ""
echo "📊 Final Status:"
if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Port 3000 still in use"
else
    echo "✅ Port 3000 is free"
fi

if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Port 8000 still in use"  
else
    echo "✅ Port 8000 is free"
fi

echo ""
echo "🎯 Dashboard stopped. You can now run ./start.sh to restart."