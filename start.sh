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
kill_port 3002

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

if ! check_port 3002; then
    echo "💡 Port 3002 still occupied. Try manually: sudo lsof -ti:3002 | xargs kill -9"
    exit 1
fi

echo "✅ Ports 3002 and 8000 are now available"

# Start backend in background
echo "🚀 Starting backend server on port 8000..."
cd backend
if [ -f "../venv/bin/activate" ]; then
    source ../venv/bin/activate
    python3 server.py &
else
    # Use system python3 if venv not available
    PYTHONPATH="/home/lucia/.local/lib/python3.12/site-packages:$PYTHONPATH" python3 server.py &
fi
BACKEND_PID=$!
cd ..

# Wait a moment for backend to start
sleep 3

# Start frontend with webpack dev server
echo "🚀 Starting frontend development server on port 3002..."
cd frontend
if [ -d "node_modules" ]; then
    npm run dev &
    FRONTEND_PID=$!
else
    echo "⚠️ Node modules not found. Installing dependencies..."
    npm install
    npm run dev &
    FRONTEND_PID=$!
fi
cd ..

# Start trading monitor daemon
echo "🤖 Starting trading monitor daemon..."
# Primeiro teste se o monitor funciona
if python3 -c "import sys; sys.path.insert(0, '.'); from trade.services.trade_monitor import TradeMonitor" 2>/dev/null; then
    # Limpar log anterior
    > monitor_trades.log
    
    # Iniciar monitor com logs direcionados para arquivo
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate && python3 monitor_daemon.py > monitor_trades.log 2>&1 &
    else
        PYTHONPATH="/home/lucia/.local/lib/python3.12/site-packages:$PYTHONPATH" python3 monitor_daemon.py > monitor_trades.log 2>&1 &
    fi
    MONITOR_PID=$!
    
    # Aguardar alguns segundos e verificar se o processo ainda está rodando
    sleep 3
    if kill -0 $MONITOR_PID 2>/dev/null; then
        echo "✅ Trading monitor daemon started successfully (PID: $MONITOR_PID)"
        echo "📋 Monitor logs: monitor_trades.log"
        
        # Iniciar tail para mostrar logs do monitor no console
        echo "🔍 Showing monitor activity in console..."
        tail -f monitor_trades.log &
        TAIL_PID=$!
    else
        echo "❌ Trading monitor daemon failed to start"
        echo "📋 Check monitor_trades.log for details"
    fi
else
    echo "❌ Trading monitor dependencies not available"
    echo "💡 Install missing dependencies or check Python path"
    MONITOR_PID=""
    TAIL_PID=""
fi

echo ""
echo "✅ All services are starting up!"
echo ""
echo "🌐 Frontend: http://localhost:3002"
echo "🔧 Backend:  http://localhost:8000"
echo "🤖 Trading:  Monitor daemon running"
echo ""
echo "Press Ctrl+C to stop all services"

# Function to cleanup processes on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down all services..."
    # Kill all services, handling empty PIDs
    if [ ! -z "$MONITOR_PID" ] && [ ! -z "$TAIL_PID" ]; then
        kill $BACKEND_PID $FRONTEND_PID $MONITOR_PID $TAIL_PID 2>/dev/null
    elif [ ! -z "$MONITOR_PID" ]; then
        kill $BACKEND_PID $FRONTEND_PID $MONITOR_PID 2>/dev/null
    else
        kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    fi
    
    # Also kill any remaining monitor processes
    pkill -f "monitor_daemon.py" 2>/dev/null
    pkill -f "tail -f monitor_trades.log" 2>/dev/null
    echo "🧹 All services stopped"
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup INT TERM

# Wait for processes
wait