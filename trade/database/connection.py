import psycopg2
from psycopg2.extras import RealDictCursor
import os
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv()

class TradeDatabase:
    def __init__(self):
        self.connection_params = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': int(os.getenv('POSTGRES_PORT', 5432)),
            'database': os.getenv('POSTGRES_DB', 'cm_bot'),
            'user': os.getenv('POSTGRES_USER', 'lucia'),
            'password': os.getenv('POSTGRES_PASSWORD', 'lucia')
        }
        self.connection = None

    def connect(self):
        """Estabelece conexão com o banco"""
        if not self.connection or self.connection.closed:
            self.connection = psycopg2.connect(
                **self.connection_params,
                cursor_factory=RealDictCursor
            )
            self.connection.autocommit = True
        return self.connection

    @contextmanager
    def get_cursor(self):
        """Context manager para cursor do banco"""
        conn = self.connect()
        cursor = conn.cursor()
        try:
            yield cursor
        finally:
            cursor.close()

    def close(self):
        """Fecha a conexão"""
        if self.connection and not self.connection.closed:
            self.connection.close()