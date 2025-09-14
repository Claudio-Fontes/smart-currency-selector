import psycopg2
from psycopg2.extras import RealDictCursor
import logging
import os
from contextlib import contextmanager
from src.config.settings import load_settings

logger = logging.getLogger(__name__)

class DatabaseConnection:
    def __init__(self):
        # Load environment variables first
        from dotenv import load_dotenv
        load_dotenv()
        
        self.settings = load_settings()
        self.connection_params = {
            'host': self.settings.get('postgres', {}).get('host', 'localhost'),
            'port': self.settings.get('postgres', {}).get('port', 5432),
            'user': self.settings.get('postgres', {}).get('user'),
            'password': self.settings.get('postgres', {}).get('password'),
            'database': self.settings.get('postgres', {}).get('database')
        }
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = None
        try:
            conn = psycopg2.connect(
                host=self.connection_params['host'],
                port=int(self.connection_params['port']), 
                user=self.connection_params['user'],
                password=self.connection_params['password'],
                database=self.connection_params['database']
            )
            yield conn
        except psycopg2.Error as e:
            logger.error(f"Database connection error: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    @contextmanager
    def get_cursor(self, commit=True):
        """Context manager for database cursor with automatic commit/rollback"""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            try:
                yield cursor
                if commit:
                    conn.commit()
            except Exception as e:
                conn.rollback()
                logger.error(f"Database operation error: {e}")
                raise
            finally:
                cursor.close()
    
    def test_connection(self):
        """Test database connection"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("SELECT version();")
                result = cursor.fetchone()
                logger.info(f"Connected to PostgreSQL: {result['version']}")
                return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

# Global database instance
db = DatabaseConnection()