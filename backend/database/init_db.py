#!/usr/bin/env python3
"""
Database initialization script for Smart Currency Selector
Run this script to create the database tables
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from dotenv import load_dotenv
from backend.database import db, token_repo

def init_database():
    """Initialize the database with required tables"""
    load_dotenv()
    
    print("🔗 Testing database connection...")
    if not db.test_connection():
        print("❌ Database connection failed. Please check your PostgreSQL settings.")
        return False
    
    print("🗃️ Initializing database schema...")
    if token_repo.init_database():
        print("✅ Database initialized successfully!")
        
        # Show some statistics
        stats = token_repo.get_statistics()
        print(f"📊 Database ready - {stats.get('total_suggestions', 0)} total suggestions")
        return True
    else:
        print("❌ Database initialization failed.")
        return False

if __name__ == "__main__":
    success = init_database()
    exit(0 if success else 1)