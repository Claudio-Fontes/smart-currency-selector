#!/bin/bash

echo "🔥 Starting Solana Hot Pools Dashboard..."

# Check if .env exists and has API key
if [ ! -f ".env" ] || ! grep -q "DEXTOOLS_API_KEY=" .env || grep -q "your_api_key_here" .env; then
    echo "❌ Please configure your DEXTOOLS_API_KEY in the .env file first"
    echo "💡 You can get an API key from: https://developer.dextools.io"
    exit 1
fi

# Function to kill processes on specific ports
kill_port() {
    local port=$1
    local pids=$(lsof -ti:$port 2>/dev/null)
    if [ ! -z "$pids" ]; then
        echo "🛑 Killing existing processes on port $port..."
        echo $pids | xargs kill -9 2>/dev/null
        sleep 1
    fi
}

# Kill any existing processes on required ports
echo "🧹 Cleaning up existing processes..."
kill_port 8000
kill_port 3000

# Wait a moment for processes to fully terminate
sleep 2

# Function to check if port is available
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "❌ Port $1 is still in use after cleanup"
        return 1
    fi
    return 0
}

# Verify ports are now available
if ! check_port 8000; then
    echo "💡 Port 8000 still occupied. Try manually: sudo lsof -ti:8000 | xargs kill -9"
    exit 1
fi

if ! check_port 3000; then
    echo "💡 Port 3000 still occupied. Try manually: sudo lsof -ti:3000 | xargs kill -9"
    exit 1
fi

echo "✅ Ports 3000 and 8000 are now available"

# Start backend in background
echo "🚀 Starting backend server on port 8000..."
cd backend
python3 server.py &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to start
sleep 3

# Start frontend
echo "🚀 Starting frontend development server on port 3000..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ Both servers are starting up!"
echo ""
echo "🌐 Frontend: http://localhost:3000"
echo "🔧 Backend:  http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop both servers"

# Function to cleanup processes on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down servers..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup INT TERM

# Wait for processes
wait