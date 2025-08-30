#!/usr/bin/env python3

import os
import sys
import time
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_backend_api():
    """Test the backend API endpoints"""
    print("🧪 Testing Backend API...")
    
    base_url = "http://localhost:8000"
    
    try:
        # Test health endpoint
        print("📡 Testing health endpoint...")
        response = requests.get(f"{base_url}/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health check passed")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
            
        # Test hot pools endpoint
        print("🔥 Testing hot pools endpoint...")
        response = requests.get(f"{base_url}/api/hot-pools?limit=5", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data['success'] and len(data['data']) > 0:
                print(f"✅ Hot pools working - Got {len(data['data'])} pools")
                
                # Test token analysis with first pool's token
                first_pool = data['data'][0]
                token_address = first_pool['mainToken']['address']
                
                print(f"🪙 Testing token analysis for {first_pool['mainToken']['symbol']}...")
                response = requests.get(f"{base_url}/api/token/{token_address}", timeout=15)
                
                if response.status_code == 200:
                    analysis = response.json()
                    if analysis['success']:
                        print("✅ Token analysis working")
                        return True
                    else:
                        print("❌ Token analysis failed - no data")
                else:
                    print(f"❌ Token analysis failed: {response.status_code}")
            else:
                print("❌ Hot pools returned no data")
        else:
            print(f"❌ Hot pools failed: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend - is it running on port 8000?")
    except Exception as e:
        print(f"❌ API test failed: {e}")
    
    return False

def check_environment():
    """Check if environment is properly configured"""
    print("🔍 Checking environment...")
    
    # Check API key
    api_key = os.getenv('DEXTOOLS_API_KEY')
    if not api_key or api_key == 'your_api_key_here':
        print("❌ DEXTOOLS_API_KEY not configured in .env")
        print("💡 Get your API key from: https://developer.dextools.io")
        return False
    else:
        print("✅ API key configured")
    
    # Check Python dependencies
    try:
        import flask
        import requests
        import flask_cors
        print("✅ Python dependencies installed")
    except ImportError as e:
        print(f"❌ Missing Python dependency: {e}")
        print("💡 Run: pip3 install -r backend/requirements.txt")
        return False
    
    # Check Node.js dependencies (if frontend folder exists)
    if os.path.exists('frontend/node_modules'):
        print("✅ Node.js dependencies installed")
    else:
        print("⚠️  Node.js dependencies not found")
        print("💡 Run: cd frontend && npm install")
    
    return True

def show_demo_info():
    """Show demo information"""
    print("\n" + "="*60)
    print("🔥 SOLANA HOT POOLS DASHBOARD - DEMO")
    print("="*60)
    print()
    print("📁 Project Structure:")
    print("   ├── frontend/          # React + Webpack")
    print("   ├── backend/           # Python Flask API")
    print("   ├── setup.sh           # Auto setup script")
    print("   └── start.sh           # Start both servers")
    print()
    print("🚀 Quick Start:")
    print("   1. ./setup.sh          # Install dependencies")
    print("   2. Configure .env      # Add your DEXTools API key")
    print("   3. ./start.sh          # Start dashboard")
    print()
    print("🌐 URLs:")
    print("   Frontend: http://localhost:3000")
    print("   Backend:  http://localhost:8000")
    print()
    print("✨ Features:")
    print("   • Real-time Solana hot pools")
    print("   • Token analysis on click (no page refresh)")
    print("   • Beautiful glassmorphism UI")
    print("   • Responsive design")
    print("   • Auto-refresh capabilities")
    print()

def main():
    show_demo_info()
    
    if not check_environment():
        print("\n❌ Environment check failed")
        print("💡 Run ./setup.sh to configure the project")
        return
    
    print("\n🧪 Running API tests...")
    
    # Check if backend is running
    try:
        response = requests.get("http://localhost:8000", timeout=2)
        if test_backend_api():
            print("\n🎉 All tests passed! Dashboard is ready to use.")
            print("🌐 Open http://localhost:3000 in your browser")
        else:
            print("\n❌ API tests failed")
    except requests.exceptions.ConnectionError:
        print("\n⚠️  Backend server not running")
        print("🚀 Start the servers with: ./start.sh")
    except Exception as e:
        print(f"\n❌ Test error: {e}")

if __name__ == "__main__":
    main()