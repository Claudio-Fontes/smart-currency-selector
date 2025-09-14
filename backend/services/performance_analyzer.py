import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
import statistics

from ..database import token_repo
from .dextools_service import DEXToolsService

logger = logging.getLogger(__name__)

class PerformanceAnalyzer:
    def __init__(self):
        self.dextools = DEXToolsService()
        self.token_repo = token_repo
        
        # Performance thresholds
        self.profit_targets = {
            'conservative': 0.15,   # 15% profit target
            'moderate': 0.30,       # 30% profit target  
            'aggressive': 0.50      # 50% profit target
        }
        
        self.stop_loss_threshold = -0.20  # 20% stop loss
        
        # Sell signal indicators
        self.sell_signals = {
            'volume_drop_threshold': 0.4,      # 40% volume drop
            'rsi_overbought': 75,              # RSI above 75
            'consecutive_red_candles': 3,      # 3 consecutive price drops
            'liquidity_drop_threshold': 0.3    # 30% liquidity drop
        }
    
    def analyze_all_suggestions(self, days_back: int = 7) -> Dict:
        """Analyze performance of all suggested tokens in the last N days"""
        try:
            # Get all suggested tokens from last N days
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            # Get unique tokens with their first suggestion
            query = """
            SELECT DISTINCT ON (token_address) 
                token_address, token_name, token_symbol,
                price_usd as entry_price,
                liquidity_usd as entry_liquidity,
                volume_24h as entry_volume,
                analysis_score,
                suggested_at as entry_time
            FROM suggested_tokens 
            WHERE suggested_at >= %s 
            ORDER BY token_address, suggested_at ASC
            """
            
            with self.token_repo.db.get_cursor() as cursor:
                cursor.execute(query, (cutoff_date,))
                suggestions = cursor.fetchall()
            
            analysis_results = []
            
            print(f"🔍 Analyzing performance of {len(suggestions)} suggested tokens...")
            
            for suggestion in suggestions:
                token_analysis = self.analyze_token_performance(dict(suggestion))
                if token_analysis:
                    analysis_results.append(token_analysis)
            
            # Generate summary statistics
            summary = self._generate_performance_summary(analysis_results)
            
            return {
                'analysis_date': datetime.now().isoformat(),
                'period_analyzed': f"{days_back} days",
                'total_tokens_analyzed': len(analysis_results),
                'summary': summary,
                'detailed_results': analysis_results,
                'recommendations': self._generate_recommendations(analysis_results)
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze suggestions performance: {e}")
            return {'error': str(e)}
    
    def analyze_token_performance(self, suggestion: Dict) -> Optional[Dict]:
        """Analyze performance of a single token suggestion"""
        try:
            token_address = suggestion['token_address']
            entry_price = float(suggestion.get('entry_price', 0))
            entry_time = suggestion['entry_time']
            
            # Skip if no entry price
            if not entry_price:
                return None
            
            print(f"📊 Analyzing {suggestion['token_symbol']} ({token_address[:8]}...)")
            
            # Get current price data
            current_data = self.dextools.get_complete_token_analysis(token_address)
            
            if not current_data.get('success'):
                print(f"❌ Failed to get current data for {suggestion['token_symbol']}")
                return None
            
            # Extract current metrics
            current_price_info = current_data.get('price', {}).get('data', {})
            current_metrics_info = current_data.get('metrics', {}).get('data', {})
            
            current_price = current_price_info.get('price', 0)
            current_liquidity = current_metrics_info.get('liquidity_usd', 0)
            current_volume_24h = current_metrics_info.get('volume_24h_usd', 0)
            
            # Calculate performance metrics
            current_price = float(current_price) if current_price else 0
            entry_price = float(entry_price) if entry_price else 0
            price_change = ((current_price - entry_price) / entry_price) * 100 if entry_price > 0 else 0
            
            # Calculate time held
            time_held = datetime.now() - entry_time
            hours_held = time_held.total_seconds() / 3600
            
            # Get price history from our database
            price_history = self.token_repo.get_token_price_evolution(token_address, hours=int(hours_held) + 24)
            
            # Calculate additional metrics
            max_profit = self._calculate_max_profit(price_history, entry_price)
            volatility = self._calculate_volatility(price_history)
            
            # Determine current status and signals
            current_status = self._determine_current_status(
                price_change, 
                current_price, 
                current_liquidity,
                current_volume_24h,
                suggestion
            )
            
            sell_signals = self._detect_sell_signals(
                price_change,
                current_price,
                current_liquidity,
                current_volume_24h,
                suggestion,
                price_history
            )
            
            return {
                'token_address': token_address,
                'symbol': suggestion['token_symbol'],
                'name': suggestion['token_name'],
                'entry_time': entry_time.isoformat(),
                'entry_price': entry_price,
                'current_price': current_price,
                'price_change_percent': round(price_change, 2),
                'max_profit_percent': round(max_profit, 2),
                'hours_held': round(hours_held, 1),
                'volatility': round(volatility, 2),
                'entry_analysis_score': suggestion.get('analysis_score', 0),
                'entry_liquidity': suggestion.get('entry_liquidity', 0),
                'current_liquidity': current_liquidity,
                'liquidity_change_percent': self._calculate_change_percent(
                    suggestion.get('entry_liquidity', 0), 
                    current_liquidity
                ),
                'entry_volume': suggestion.get('entry_volume', 0),
                'current_volume': current_volume_24h,
                'volume_change_percent': self._calculate_change_percent(
                    suggestion.get('entry_volume', 0),
                    current_volume_24h
                ),
                'current_status': current_status,
                'sell_signals': sell_signals,
                'recommendation': self._generate_token_recommendation(
                    price_change, max_profit, sell_signals, current_status
                )
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze token {suggestion.get('token_symbol', 'unknown')}: {e}")
            return None
    
    def _calculate_max_profit(self, price_history: List[Dict], entry_price: float) -> float:
        """Calculate maximum profit achieved since entry"""
        if not price_history or entry_price <= 0:
            return 0
        
        max_price = entry_price
        for record in price_history:
            price = float(record.get('price_usd', 0))
            if price > max_price:
                max_price = price
        
        return ((max_price - entry_price) / entry_price) * 100
    
    def _calculate_volatility(self, price_history: List[Dict]) -> float:
        """Calculate price volatility"""
        if len(price_history) < 2:
            return 0
        
        prices = [float(record.get('price_usd', 0)) for record in price_history if record.get('price_usd')]
        if len(prices) < 2:
            return 0
        
        # Calculate percentage changes
        changes = []
        for i in range(1, len(prices)):
            if prices[i-1] > 0:
                change = ((prices[i] - prices[i-1]) / prices[i-1]) * 100
                changes.append(abs(change))
        
        return statistics.mean(changes) if changes else 0
    
    def _calculate_change_percent(self, old_value: float, new_value: float) -> float:
        """Calculate percentage change between two values"""
        if not old_value or old_value <= 0:
            return 0
        return ((new_value - old_value) / old_value) * 100
    
    def _determine_current_status(self, price_change: float, current_price: float, 
                                current_liquidity: float, current_volume: float,
                                suggestion: Dict) -> str:
        """Determine current investment status"""
        if price_change >= self.profit_targets['aggressive']:
            return 'excellent_profit'
        elif price_change >= self.profit_targets['moderate']:
            return 'good_profit'
        elif price_change >= self.profit_targets['conservative']:
            return 'moderate_profit'
        elif price_change > 0:
            return 'small_profit'
        elif price_change >= self.stop_loss_threshold * 100:
            return 'small_loss'
        else:
            return 'significant_loss'
    
    def _detect_sell_signals(self, price_change: float, current_price: float,
                           current_liquidity: float, current_volume: float,
                           suggestion: Dict, price_history: List[Dict]) -> List[str]:
        """Detect sell signals based on various indicators"""
        signals = []
        
        # Profit target signals
        if price_change >= self.profit_targets['aggressive']:
            signals.append('profit_target_aggressive_reached')
        elif price_change >= self.profit_targets['moderate']:
            signals.append('profit_target_moderate_reached')
        elif price_change >= self.profit_targets['conservative']:
            signals.append('profit_target_conservative_reached')
        
        # Stop loss signal
        if price_change <= self.stop_loss_threshold * 100:
            signals.append('stop_loss_triggered')
        
        # Volume drop signal
        entry_volume = suggestion.get('entry_volume', 0)
        if entry_volume > 0:
            volume_change = (current_volume - entry_volume) / entry_volume
            if volume_change <= -self.sell_signals['volume_drop_threshold']:
                signals.append('volume_dropping')
        
        # Liquidity drop signal
        entry_liquidity = suggestion.get('entry_liquidity', 0)
        if entry_liquidity > 0:
            liquidity_change = (current_liquidity - entry_liquidity) / entry_liquidity
            if liquidity_change <= -self.sell_signals['liquidity_drop_threshold']:
                signals.append('liquidity_dropping')
        
        # Consecutive price drops
        if len(price_history) >= 3:
            recent_prices = [float(h.get('price_usd', 0)) for h in price_history[-3:]]
            if len(recent_prices) == 3 and all(recent_prices[i] > recent_prices[i+1] for i in range(2)):
                signals.append('consecutive_price_drops')
        
        return signals
    
    def _generate_token_recommendation(self, price_change: float, max_profit: float,
                                     sell_signals: List[str], status: str) -> Dict:
        """Generate buy/hold/sell recommendation for a token"""
        
        # Strong sell signals
        strong_sell_signals = [
            'stop_loss_triggered', 
            'profit_target_aggressive_reached',
            'liquidity_dropping'
        ]
        
        # Moderate sell signals  
        moderate_sell_signals = [
            'profit_target_moderate_reached',
            'volume_dropping',
            'consecutive_price_drops'
        ]
        
        # Conservative sell signals
        conservative_sell_signals = [
            'profit_target_conservative_reached'
        ]
        
        if any(signal in sell_signals for signal in strong_sell_signals):
            action = 'STRONG_SELL'
            confidence = 'high'
            reason = 'Multiple strong sell indicators detected'
        elif any(signal in sell_signals for signal in moderate_sell_signals):
            action = 'SELL'
            confidence = 'medium'
            reason = 'Moderate sell signals present'
        elif any(signal in sell_signals for signal in conservative_sell_signals):
            action = 'CONSIDER_SELL'
            confidence = 'medium'
            reason = 'Conservative profit target reached'
        elif status == 'small_loss' and max_profit > 20:
            action = 'HOLD'
            confidence = 'medium'  
            reason = f'Small loss but token showed {max_profit:.1f}% max profit potential'
        elif status == 'significant_loss':
            action = 'SELL'
            confidence = 'high'
            reason = 'Cut losses to preserve capital'
        else:
            action = 'HOLD'
            confidence = 'low'
            reason = 'No clear signals, continue monitoring'
        
        return {
            'action': action,
            'confidence': confidence,
            'reason': reason,
            'signals_detected': sell_signals
        }
    
    def _generate_performance_summary(self, results: List[Dict]) -> Dict:
        """Generate summary statistics of all analyzed tokens"""
        if not results:
            return {}
        
        profitable_tokens = [r for r in results if r['price_change_percent'] > 0]
        losing_tokens = [r for r in results if r['price_change_percent'] < 0]
        
        total_return = sum(r['price_change_percent'] for r in results)
        avg_return = total_return / len(results)
        
        max_winner = max(results, key=lambda x: x['price_change_percent'])
        max_loser = min(results, key=lambda x: x['price_change_percent'])
        
        return {
            'total_tokens': len(results),
            'profitable_tokens': len(profitable_tokens),
            'losing_tokens': len(losing_tokens),
            'win_rate': round((len(profitable_tokens) / len(results)) * 100, 1),
            'average_return': round(avg_return, 2),
            'total_return': round(total_return, 2),
            'best_performer': {
                'symbol': max_winner['symbol'],
                'return': max_winner['price_change_percent']
            },
            'worst_performer': {
                'symbol': max_loser['symbol'],
                'return': max_loser['price_change_percent']
            },
            'tokens_with_sell_signals': len([r for r in results if r['sell_signals']]),
            'average_max_profit': round(statistics.mean([r['max_profit_percent'] for r in results]), 2),
            'average_volatility': round(statistics.mean([r['volatility'] for r in results]), 2)
        }
    
    def _generate_recommendations(self, results: List[Dict]) -> Dict:
        """Generate overall recommendations based on analysis"""
        if not results:
            return {}
        
        strong_sells = [r for r in results if r['recommendation']['action'] == 'STRONG_SELL']
        sells = [r for r in results if r['recommendation']['action'] == 'SELL']
        consider_sells = [r for r in results if r['recommendation']['action'] == 'CONSIDER_SELL']
        holds = [r for r in results if r['recommendation']['action'] == 'HOLD']
        
        return {
            'immediate_actions_required': len(strong_sells) + len(sells),
            'strong_sell_tokens': [{'symbol': r['symbol'], 'reason': r['recommendation']['reason']} for r in strong_sells],
            'sell_tokens': [{'symbol': r['symbol'], 'reason': r['recommendation']['reason']} for r in sells],
            'consider_sell_tokens': [{'symbol': r['symbol'], 'reason': r['recommendation']['reason']} for r in consider_sells],
            'hold_tokens': len(holds),
            'portfolio_health': self._assess_portfolio_health(results)
        }
    
    def _assess_portfolio_health(self, results: List[Dict]) -> str:
        """Assess overall portfolio health"""
        if not results:
            return 'unknown'
        
        avg_return = statistics.mean([r['price_change_percent'] for r in results])
        win_rate = len([r for r in results if r['price_change_percent'] > 0]) / len(results)
        
        if avg_return > 15 and win_rate > 0.6:
            return 'excellent'
        elif avg_return > 5 and win_rate > 0.5:
            return 'good'
        elif avg_return > 0 and win_rate > 0.4:
            return 'fair'
        else:
            return 'poor'

# Global analyzer instance
performance_analyzer = PerformanceAnalyzer()