import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from decimal import Decimal
import json

from .db_connection import db

logger = logging.getLogger(__name__)

class TokenRepository:
    def __init__(self):
        self.db = db
    
    def init_database(self):
        """Initialize database tables"""
        try:
            schema_file = "/mnt/c/workspace/smart-currency-selector/backend/database/schema.sql"
            with open(schema_file, 'r') as f:
                schema_sql = f.read()
            
            with self.db.get_cursor() as cursor:
                cursor.execute(schema_sql)
                logger.info("Database schema initialized successfully")
                return True
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            return False
    
    def save_suggested_token(self, token_data: Dict[str, Any]) -> bool:
        """Save a suggested token to the database"""
        try:
            insert_sql = """
            INSERT INTO suggested_tokens (
                token_address, token_name, token_symbol, chain,
                price_usd, price_change_24h, volume_24h, liquidity_usd, market_cap,
                pool_score, liquidity_locked, is_audited, honeypot_risk,
                holder_count, top_10_holders_percentage, concentration_risk,
                price_trend, trend_confidence,
                pool_address, pool_created_at, dex_name,
                suggestion_reason, analysis_score, risk_level,
                raw_data
            ) VALUES (
                %(token_address)s, %(token_name)s, %(token_symbol)s, %(chain)s,
                %(price_usd)s, %(price_change_24h)s, %(volume_24h)s, %(liquidity_usd)s, %(market_cap)s,
                %(pool_score)s, %(liquidity_locked)s, %(is_audited)s, %(honeypot_risk)s,
                %(holder_count)s, %(top_10_holders_percentage)s, %(concentration_risk)s,
                %(price_trend)s, %(trend_confidence)s,
                %(pool_address)s, %(pool_created_at)s, %(dex_name)s,
                %(suggestion_reason)s, %(analysis_score)s, %(risk_level)s,
                %(raw_data)s
            )
            """
            
            # Parse and validate token data
            parsed_data = self._parse_token_data(token_data)
            
            with self.db.get_cursor() as cursor:
                cursor.execute(insert_sql, parsed_data)
                logger.info(f"Saved token {parsed_data['token_address']} to database")
                return True
                
        except Exception as e:
            logger.error(f"Failed to save token {token_data.get('token_address', 'unknown')}: {e}")
            return False
    
    def _parse_token_data(self, token_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse and validate token data for database insertion"""
        def safe_decimal(value, default=None):
            """Safely convert to Decimal"""
            if value is None:
                return default
            try:
                return Decimal(str(value))
            except:
                return default
        
        def safe_int(value, default=None):
            """Safely convert to int"""
            if value is None:
                return default
            try:
                return int(value)
            except:
                return default
        
        def safe_bool(value, default=None):
            """Safely convert to bool"""
            if value is None:
                return default
            if isinstance(value, bool):
                return value
            return str(value).lower() in ['true', '1', 'yes', 'on']
        
        def safe_timestamp(value, default=None):
            """Safely convert to timestamp"""
            if value is None:
                return default
            if isinstance(value, datetime):
                return value
            try:
                return datetime.fromisoformat(str(value))
            except:
                return default
        
        return {
            'token_address': token_data.get('address', token_data.get('token_address')),
            'token_name': token_data.get('name', token_data.get('token_name')),
            'token_symbol': token_data.get('symbol', token_data.get('token_symbol')),
            'chain': token_data.get('chain', 'solana'),
            
            # Price metrics
            'price_usd': safe_decimal(token_data.get('price')),
            'price_change_24h': safe_decimal(token_data.get('price_change_24h')),
            'volume_24h': safe_decimal(token_data.get('volume_24h')),
            'liquidity_usd': safe_decimal(token_data.get('liquidity')),
            'market_cap': safe_decimal(token_data.get('market_cap')),
            
            # Security metrics
            'pool_score': safe_int(token_data.get('pool_score')),
            'liquidity_locked': safe_bool(token_data.get('liquidity_locked')),
            'is_audited': safe_bool(token_data.get('is_audited')),
            'honeypot_risk': safe_bool(token_data.get('honeypot_risk')),
            
            # Holders analysis
            'holder_count': safe_int(token_data.get('holder_count')),
            'top_10_holders_percentage': safe_decimal(token_data.get('top_10_holders_percentage')),
            'concentration_risk': token_data.get('concentration_risk'),
            
            # Price trend
            'price_trend': token_data.get('price_trend'),
            'trend_confidence': safe_decimal(token_data.get('trend_confidence')),
            
            # Pool info
            'pool_address': token_data.get('pool_address'),
            'pool_created_at': safe_timestamp(token_data.get('pool_created_at')),
            'dex_name': token_data.get('dex_name', token_data.get('exchange')),
            
            # Analysis metadata
            'suggestion_reason': token_data.get('suggestion_reason', 'AI Analysis'),
            'analysis_score': safe_decimal(token_data.get('analysis_score', token_data.get('score'))),
            'risk_level': token_data.get('risk_level', 'medium'),
            
            # Store all raw data as JSON
            'raw_data': json.dumps(token_data)
        }
    
    def get_recent_suggestions(self, limit: int = 100, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent suggested tokens"""
        try:
            query = """
            SELECT * FROM suggested_tokens 
            WHERE suggested_at >= NOW() - INTERVAL '%s hours'
            ORDER BY suggested_at DESC, analysis_score DESC NULLS LAST
            LIMIT %s
            """
            
            with self.db.get_cursor() as cursor:
                cursor.execute(query, (hours, limit))
                results = cursor.fetchall()
                return [dict(row) for row in results]
                
        except Exception as e:
            logger.error(f"Failed to get recent suggestions: {e}")
            return []
    
    def get_token_history(self, token_address: str, chain: str = 'solana') -> List[Dict[str, Any]]:
        """Get history for a specific token"""
        try:
            query = """
            SELECT * FROM suggested_tokens 
            WHERE token_address = %s AND chain = %s
            ORDER BY suggested_at DESC
            """
            
            with self.db.get_cursor() as cursor:
                cursor.execute(query, (token_address, chain))
                results = cursor.fetchall()
                return [dict(row) for row in results]
                
        except Exception as e:
            logger.error(f"Failed to get token history: {e}")
            return []
    
    def get_token_price_evolution(self, token_address: str, chain: str = 'solana', hours: int = 24) -> List[Dict[str, Any]]:
        """Get price evolution history for a specific token"""
        try:
            query = """
            SELECT 
                suggested_at,
                price_usd,
                price_change_24h,
                volume_24h,
                liquidity_usd,
                analysis_score,
                suggestion_reason
            FROM suggested_tokens 
            WHERE token_address = %s AND chain = %s AND suggested_at >= NOW() - INTERVAL '%s hours'
            ORDER BY suggested_at ASC
            """
            
            with self.db.get_cursor() as cursor:
                cursor.execute(query, (token_address, chain, hours))
                results = cursor.fetchall()
                return [dict(row) for row in results]
                
        except Exception as e:
            logger.error(f"Failed to get price evolution: {e}")
            return []

    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            stats_query = """
            SELECT 
                COUNT(*) as total_suggestions,
                COUNT(DISTINCT token_address) as unique_tokens,
                AVG(analysis_score) as avg_score,
                COUNT(*) FILTER (WHERE suggested_at >= NOW() - INTERVAL '24 hours') as suggestions_24h,
                COUNT(*) FILTER (WHERE risk_level = 'low') as low_risk_count,
                COUNT(*) FILTER (WHERE risk_level = 'medium') as medium_risk_count,
                COUNT(*) FILTER (WHERE risk_level = 'high') as high_risk_count,
                COUNT(*) FILTER (WHERE suggested_at >= NOW() - INTERVAL '1 hour') as suggestions_1h
            FROM suggested_tokens
            """
            
            with self.db.get_cursor() as cursor:
                cursor.execute(stats_query)
                result = cursor.fetchone()
                return dict(result) if result else {}
                
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}

# Global repository instance
token_repo = TokenRepository()