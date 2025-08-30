#!/usr/bin/env python3

import os
import sys
from flask import Flask
from flask_cors import CORS

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.api.routes import api

def create_app():
    app = Flask(__name__)
    
    # Enable CORS for all routes
    CORS(app, origins=['http://localhost:3000'])
    
    # Register API blueprint
    app.register_blueprint(api, url_prefix='/api')
    
    @app.route('/')
    def home():
        return {
            'message': '🔥 Solana Hot Pools API',
            'version': '1.0.0',
            'endpoints': {
                '/api/hot-pools': 'GET - Fetch hot pools with optional ?limit parameter',
                '/api/token/<address>': 'GET - Get detailed token analysis',
                '/api/health': 'GET - Health check'
            }
        }
    
    return app

if __name__ == '__main__':
    app = create_app()
    print("🔥 Starting Solana Hot Pools API server...")
    print("🌐 Frontend: http://localhost:3000")
    print("🔧 API: http://localhost:8000")
    app.run(host='0.0.0.0', port=8000, debug=True)