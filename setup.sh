#!/bin/bash

echo "🔥 Setting up Solana Hot Pools Dashboard..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js first."
    exit 1
fi

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

# Install backend dependencies
echo "📦 Installing backend dependencies..."
cd backend
pip3 install -r requirements.txt
cd ..

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
cd frontend
npm install
cd ..

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file..."
    cat > .env << EOL
# DEXTools API Configuration
DEXTOOLS_API_KEY=your_api_key_here
DEXTOOLS_BASE_URL=https://public-api.dextools.io/standard/v2

# Server Configuration
FRONTEND_PORT=3000
BACKEND_PORT=8000
EOL
    echo "⚠️  Please update the .env file with your DEXTools API key"
fi

echo "✅ Setup complete!"
echo ""
echo "🚀 To start the application:"
echo "   Backend:  npm run serve (or python3 backend/server.py)"
echo "   Frontend: npm run dev"
echo ""
echo "🌐 URLs:"
echo "   Frontend: http://localhost:3000"
echo "   Backend:  http://localhost:8000"