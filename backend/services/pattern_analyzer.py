import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import statistics
import json

from ..database import token_repo

logger = logging.getLogger(__name__)

class PatternAnalyzer:
    """Analyzes patterns between winning and losing token suggestions"""
    
    def __init__(self):
        self.token_repo = token_repo
    
    def analyze_patterns(self, days_back: int = 7) -> Dict:
        """Analyze patterns between winners and losers"""
        try:
            print("🔍 Analyzing patterns in token performance...")
            
            # Get all tokens with their initial and latest data
            tokens_data = self._get_tokens_with_performance(days_back)
            
            if not tokens_data:
                return {'error': 'No tokens found for analysis'}
            
            # Categorize tokens
            strong_winners = []  # >30% gain
            moderate_winners = []  # 10-30% gain
            small_winners = []  # 0-10% gain
            small_losers = []  # 0 to -10% loss
            moderate_losers = []  # -10 to -30% loss
            big_losers = []  # <-30% loss
            
            for token in tokens_data:
                change = token['price_change_percent']
                if change > 30:
                    strong_winners.append(token)
                elif change > 10:
                    moderate_winners.append(token)
                elif change > 0:
                    small_winners.append(token)
                elif change > -10:
                    small_losers.append(token)
                elif change > -30:
                    moderate_losers.append(token)
                else:
                    big_losers.append(token)
            
            # Analyze patterns
            patterns = {
                'analysis_date': datetime.now().isoformat(),
                'period_analyzed': f'{days_back} days',
                'total_tokens': len(tokens_data),
                'categories': {
                    'strong_winners': len(strong_winners),
                    'moderate_winners': len(moderate_winners),
                    'small_winners': len(small_winners),
                    'small_losers': len(small_losers),
                    'moderate_losers': len(moderate_losers),
                    'big_losers': len(big_losers)
                },
                'winner_characteristics': self._analyze_group_characteristics(
                    strong_winners + moderate_winners, 'Winners (>10% gain)'
                ),
                'loser_characteristics': self._analyze_group_characteristics(
                    moderate_losers + big_losers, 'Losers (>10% loss)'
                ),
                'comparative_analysis': self._compare_winners_vs_losers(
                    strong_winners + moderate_winners,
                    moderate_losers + big_losers
                ),
                'key_insights': self._generate_key_insights(
                    strong_winners, moderate_winners, small_winners,
                    small_losers, moderate_losers, big_losers
                ),
                'recommended_criteria_adjustments': self._suggest_criteria_improvements(
                    strong_winners + moderate_winners,
                    moderate_losers + big_losers
                )
            }
            
            return patterns
            
        except Exception as e:
            logger.error(f"Pattern analysis failed: {e}")
            return {'error': str(e)}
    
    def _get_tokens_with_performance(self, days_back: int) -> List[Dict]:
        """Get all tokens with their performance data"""
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        query = """
        WITH first_entries AS (
            SELECT DISTINCT ON (token_address) 
                token_address,
                token_name,
                token_symbol,
                price_usd as entry_price,
                liquidity_usd as entry_liquidity,
                volume_24h as entry_volume,
                pool_score as entry_score,
                market_cap as entry_market_cap,
                holder_count as entry_holders,
                analysis_score,
                risk_level,
                price_trend as entry_trend,
                suggested_at as entry_time,
                raw_data
            FROM suggested_tokens 
            WHERE suggested_at >= %s 
            ORDER BY token_address, suggested_at ASC
        ),
        latest_entries AS (
            SELECT DISTINCT ON (token_address)
                token_address,
                price_usd as latest_price,
                liquidity_usd as latest_liquidity,
                volume_24h as latest_volume,
                suggested_at as latest_time
            FROM suggested_tokens
            WHERE suggested_at >= %s
            ORDER BY token_address, suggested_at DESC
        )
        SELECT 
            f.*,
            l.latest_price,
            l.latest_liquidity,
            l.latest_volume,
            l.latest_time
        FROM first_entries f
        JOIN latest_entries l ON f.token_address = l.token_address
        """
        
        with self.token_repo.db.get_cursor() as cursor:
            cursor.execute(query, (cutoff_date, cutoff_date))
            results = cursor.fetchall()
        
        tokens_data = []
        for row in results:
            entry_price = float(row['entry_price']) if row['entry_price'] else 0
            latest_price = float(row['latest_price']) if row['latest_price'] else 0
            
            if entry_price > 0:
                price_change = ((latest_price - entry_price) / entry_price) * 100
                
                # Parse raw_data for additional metrics
                raw_data = {}
                if row['raw_data']:
                    try:
                        raw_data = json.loads(row['raw_data'])
                    except:
                        pass
                
                tokens_data.append({
                    'token_address': row['token_address'],
                    'symbol': row['token_symbol'],
                    'name': row['token_name'],
                    'entry_price': entry_price,
                    'latest_price': latest_price,
                    'price_change_percent': price_change,
                    'entry_liquidity': float(row['entry_liquidity']) if row['entry_liquidity'] else 0,
                    'latest_liquidity': float(row['latest_liquidity']) if row['latest_liquidity'] else 0,
                    'entry_volume': float(row['entry_volume']) if row['entry_volume'] else 0,
                    'latest_volume': float(row['latest_volume']) if row['latest_volume'] else 0,
                    'entry_score': row['entry_score'],
                    'entry_market_cap': float(row['entry_market_cap']) if row['entry_market_cap'] else 0,
                    'entry_holders': row['entry_holders'],
                    'analysis_score': float(row['analysis_score']) if row['analysis_score'] else 0,
                    'risk_level': row['risk_level'],
                    'entry_trend': row['entry_trend'],
                    'time_held_hours': (row['latest_time'] - row['entry_time']).total_seconds() / 3600,
                    'age_at_entry_hours': self._get_age_at_entry(raw_data),
                    'pool_rank': raw_data.get('pool_rank', 999)
                })
        
        return tokens_data
    
    def _get_age_at_entry(self, raw_data: Dict) -> float:
        """Extract token age at entry from raw data"""
        age_hours = raw_data.get('age_hours', 0)
        if age_hours:
            return float(age_hours)
        return 0
    
    def _analyze_group_characteristics(self, tokens: List[Dict], group_name: str) -> Dict:
        """Analyze characteristics of a group of tokens"""
        if not tokens:
            return {}
        
        return {
            'group_name': group_name,
            'count': len(tokens),
            'avg_metrics': {
                'avg_analysis_score': self._safe_mean([t['analysis_score'] for t in tokens]),
                'avg_entry_liquidity': self._safe_mean([t['entry_liquidity'] for t in tokens]),
                'avg_entry_volume': self._safe_mean([t['entry_volume'] for t in tokens]),
                'avg_entry_market_cap': self._safe_mean([t['entry_market_cap'] for t in tokens]),
                'avg_entry_holders': self._safe_mean([t['entry_holders'] for t in tokens if t['entry_holders']]),
                'avg_age_at_entry_hours': self._safe_mean([t['age_at_entry_hours'] for t in tokens if t['age_at_entry_hours'] > 0]),
                'avg_pool_rank': self._safe_mean([t['pool_rank'] for t in tokens if t['pool_rank'] < 999]),
                'avg_time_held_hours': self._safe_mean([t['time_held_hours'] for t in tokens])
            },
            'median_metrics': {
                'median_analysis_score': self._safe_median([t['analysis_score'] for t in tokens]),
                'median_entry_liquidity': self._safe_median([t['entry_liquidity'] for t in tokens]),
                'median_entry_volume': self._safe_median([t['entry_volume'] for t in tokens]),
                'median_entry_market_cap': self._safe_median([t['entry_market_cap'] for t in tokens])
            },
            'risk_distribution': self._count_risk_levels(tokens),
            'trend_distribution': self._count_trends(tokens),
            'liquidity_change': {
                'avg_liquidity_change_percent': self._calculate_avg_liquidity_change(tokens),
                'tokens_with_increased_liquidity': sum(1 for t in tokens if t['latest_liquidity'] > t['entry_liquidity']),
                'tokens_with_decreased_liquidity': sum(1 for t in tokens if t['latest_liquidity'] < t['entry_liquidity'])
            },
            'volume_change': {
                'avg_volume_change_percent': self._calculate_avg_volume_change(tokens),
                'tokens_with_increased_volume': sum(1 for t in tokens if t['latest_volume'] > t['entry_volume']),
                'tokens_with_decreased_volume': sum(1 for t in tokens if t['latest_volume'] < t['entry_volume'])
            }
        }
    
    def _compare_winners_vs_losers(self, winners: List[Dict], losers: List[Dict]) -> Dict:
        """Compare characteristics between winners and losers"""
        if not winners or not losers:
            return {}
        
        winner_chars = self._analyze_group_characteristics(winners, 'Winners')
        loser_chars = self._analyze_group_characteristics(losers, 'Losers')
        
        comparisons = {
            'key_differences': {},
            'success_indicators': [],
            'failure_indicators': []
        }
        
        # Compare average metrics
        w_avg = winner_chars['avg_metrics']
        l_avg = loser_chars['avg_metrics']
        
        # Analysis score difference
        score_diff = w_avg['avg_analysis_score'] - l_avg['avg_analysis_score']
        if abs(score_diff) > 5:
            comparisons['key_differences']['analysis_score'] = {
                'winners_avg': round(w_avg['avg_analysis_score'], 2),
                'losers_avg': round(l_avg['avg_analysis_score'], 2),
                'difference': round(score_diff, 2),
                'insight': 'Winners had significantly higher analysis scores' if score_diff > 0 else 'Losers had higher analysis scores'
            }
        
        # Liquidity difference
        liq_diff_pct = ((w_avg['avg_entry_liquidity'] - l_avg['avg_entry_liquidity']) / l_avg['avg_entry_liquidity'] * 100) if l_avg['avg_entry_liquidity'] > 0 else 0
        if abs(liq_diff_pct) > 20:
            comparisons['key_differences']['liquidity'] = {
                'winners_avg': round(w_avg['avg_entry_liquidity'], 2),
                'losers_avg': round(l_avg['avg_entry_liquidity'], 2),
                'difference_percent': round(liq_diff_pct, 2),
                'insight': f'Winners had {abs(liq_diff_pct):.1f}% {"higher" if liq_diff_pct > 0 else "lower"} initial liquidity'
            }
        
        # Volume difference
        vol_diff_pct = ((w_avg['avg_entry_volume'] - l_avg['avg_entry_volume']) / l_avg['avg_entry_volume'] * 100) if l_avg['avg_entry_volume'] > 0 else 0
        if abs(vol_diff_pct) > 20:
            comparisons['key_differences']['volume'] = {
                'winners_avg': round(w_avg['avg_entry_volume'], 2),
                'losers_avg': round(l_avg['avg_entry_volume'], 2),
                'difference_percent': round(vol_diff_pct, 2),
                'insight': f'Winners had {abs(vol_diff_pct):.1f}% {"higher" if vol_diff_pct > 0 else "lower"} initial volume'
            }
        
        # Age difference
        age_diff = w_avg['avg_age_at_entry_hours'] - l_avg['avg_age_at_entry_hours']
        if abs(age_diff) > 24:
            comparisons['key_differences']['token_age'] = {
                'winners_avg_hours': round(w_avg['avg_age_at_entry_hours'], 1),
                'losers_avg_hours': round(l_avg['avg_age_at_entry_hours'], 1),
                'difference_hours': round(age_diff, 1),
                'insight': f'Winners were {"older" if age_diff > 0 else "younger"} tokens on average'
            }
        
        # Pool rank difference
        rank_diff = w_avg['avg_pool_rank'] - l_avg['avg_pool_rank']
        if abs(rank_diff) > 3:
            comparisons['key_differences']['pool_rank'] = {
                'winners_avg': round(w_avg['avg_pool_rank'], 1),
                'losers_avg': round(l_avg['avg_pool_rank'], 1),
                'difference': round(rank_diff, 1),
                'insight': f'Winners had {"better" if rank_diff < 0 else "worse"} pool rankings'
            }
        
        # Identify success indicators
        if w_avg['avg_analysis_score'] > 70:
            comparisons['success_indicators'].append(f"High analysis score (>{70})")
        if w_avg['avg_entry_liquidity'] > 50000:
            comparisons['success_indicators'].append(f"High initial liquidity (>${w_avg['avg_entry_liquidity']:.0f})")
        if w_avg['avg_entry_volume'] > 20000:
            comparisons['success_indicators'].append(f"High initial volume (>${w_avg['avg_entry_volume']:.0f})")
        if w_avg['avg_age_at_entry_hours'] < 100:
            comparisons['success_indicators'].append(f"Caught early (<{w_avg['avg_age_at_entry_hours']:.0f} hours old)")
        
        # Identify failure indicators
        if l_avg['avg_analysis_score'] < 60:
            comparisons['failure_indicators'].append(f"Low analysis score (<60)")
        if l_avg['avg_entry_liquidity'] < 10000:
            comparisons['failure_indicators'].append(f"Low initial liquidity (<$10,000)")
        if l_avg['avg_entry_volume'] < 5000:
            comparisons['failure_indicators'].append(f"Low initial volume (<$5,000)")
        if l_avg['avg_age_at_entry_hours'] > 200:
            comparisons['failure_indicators'].append(f"Token too old (>{l_avg['avg_age_at_entry_hours']:.0f} hours)")
        
        return comparisons
    
    def _generate_key_insights(self, strong_winners, moderate_winners, small_winners,
                              small_losers, moderate_losers, big_losers) -> List[str]:
        """Generate key insights from the analysis"""
        insights = []
        
        all_winners = strong_winners + moderate_winners + small_winners
        all_losers = small_losers + moderate_losers + big_losers
        
        if all_winners and all_losers:
            # Win rate insight
            win_rate = len(all_winners) / (len(all_winners) + len(all_losers)) * 100
            insights.append(f"Overall win rate: {win_rate:.1f}%")
            
            # Strong performance insight
            if strong_winners:
                strong_rate = len(strong_winners) / (len(all_winners) + len(all_losers)) * 100
                insights.append(f"{strong_rate:.1f}% of all tokens achieved >30% gains")
            
            # Risk insight
            if big_losers:
                big_loss_rate = len(big_losers) / (len(all_winners) + len(all_losers)) * 100
                insights.append(f"⚠️ {big_loss_rate:.1f}% of tokens had severe losses (>30%)")
            
            # Liquidity insights
            winner_liq_avg = self._safe_mean([t['entry_liquidity'] for t in all_winners])
            loser_liq_avg = self._safe_mean([t['entry_liquidity'] for t in all_losers])
            if winner_liq_avg > loser_liq_avg * 1.5:
                insights.append(f"✅ Winners had {(winner_liq_avg/loser_liq_avg):.1f}x higher initial liquidity")
            
            # Volume insights
            winner_vol_avg = self._safe_mean([t['entry_volume'] for t in all_winners])
            loser_vol_avg = self._safe_mean([t['entry_volume'] for t in all_losers])
            if winner_vol_avg > loser_vol_avg * 1.5:
                insights.append(f"✅ Winners had {(winner_vol_avg/loser_vol_avg):.1f}x higher initial volume")
            
            # Age insights
            winner_age_avg = self._safe_mean([t['age_at_entry_hours'] for t in all_winners if t['age_at_entry_hours'] > 0])
            loser_age_avg = self._safe_mean([t['age_at_entry_hours'] for t in all_losers if t['age_at_entry_hours'] > 0])
            if winner_age_avg < loser_age_avg * 0.7:
                insights.append(f"✅ Winners were caught {(loser_age_avg/winner_age_avg):.1f}x earlier than losers")
            
            # Score insights
            winner_score_avg = self._safe_mean([t['analysis_score'] for t in all_winners])
            loser_score_avg = self._safe_mean([t['analysis_score'] for t in all_losers])
            if winner_score_avg > loser_score_avg * 1.2:
                insights.append(f"✅ Winners had {((winner_score_avg-loser_score_avg)/loser_score_avg*100):.1f}% higher analysis scores")
        
        return insights
    
    def _suggest_criteria_improvements(self, winners: List[Dict], losers: List[Dict]) -> Dict:
        """Suggest improvements to selection criteria based on patterns"""
        suggestions = {
            'current_performance': {},
            'recommended_changes': [],
            'new_thresholds': {}
        }
        
        if not winners or not losers:
            return suggestions
        
        # Calculate current performance
        total = len(winners) + len(losers)
        win_rate = len(winners) / total * 100
        suggestions['current_performance'] = {
            'win_rate': round(win_rate, 1),
            'total_analyzed': total,
            'winners': len(winners),
            'losers': len(losers)
        }
        
        # Analyze what worked
        winner_chars = {
            'min_liquidity': min([t['entry_liquidity'] for t in winners]),
            'avg_liquidity': self._safe_mean([t['entry_liquidity'] for t in winners]),
            'min_volume': min([t['entry_volume'] for t in winners]),
            'avg_volume': self._safe_mean([t['entry_volume'] for t in winners]),
            'min_score': min([t['analysis_score'] for t in winners]),
            'avg_score': self._safe_mean([t['analysis_score'] for t in winners]),
            'max_age': max([t['age_at_entry_hours'] for t in winners if t['age_at_entry_hours'] > 0] or [0]),
            'avg_age': self._safe_mean([t['age_at_entry_hours'] for t in winners if t['age_at_entry_hours'] > 0])
        }
        
        # Analyze what failed
        loser_chars = {
            'max_liquidity': max([t['entry_liquidity'] for t in losers]),
            'avg_liquidity': self._safe_mean([t['entry_liquidity'] for t in losers]),
            'max_volume': max([t['entry_volume'] for t in losers]),
            'avg_volume': self._safe_mean([t['entry_volume'] for t in losers]),
            'max_score': max([t['analysis_score'] for t in losers]),
            'avg_score': self._safe_mean([t['analysis_score'] for t in losers]),
            'min_age': min([t['age_at_entry_hours'] for t in losers if t['age_at_entry_hours'] > 0] or [999]),
            'avg_age': self._safe_mean([t['age_at_entry_hours'] for t in losers if t['age_at_entry_hours'] > 0])
        }
        
        # Generate specific recommendations
        
        # Liquidity threshold
        if winner_chars['min_liquidity'] > 15000 and loser_chars['avg_liquidity'] < 15000:
            suggestions['recommended_changes'].append(
                f"Increase minimum liquidity from $10,000 to ${winner_chars['min_liquidity']:.0f}"
            )
            suggestions['new_thresholds']['min_liquidity'] = winner_chars['min_liquidity']
        
        # Volume threshold
        if winner_chars['min_volume'] > 10000 and loser_chars['avg_volume'] < 10000:
            suggestions['recommended_changes'].append(
                f"Increase minimum volume from $5,000 to ${winner_chars['min_volume']:.0f}"
            )
            suggestions['new_thresholds']['min_volume_24h'] = winner_chars['min_volume']
        
        # Score threshold
        if winner_chars['min_score'] > 75 and loser_chars['avg_score'] < 70:
            suggestions['recommended_changes'].append(
                f"Increase minimum DEXT score from 70 to {winner_chars['min_score']:.0f}"
            )
            suggestions['new_thresholds']['min_dext_score'] = winner_chars['min_score']
        
        # Age threshold
        if winner_chars['avg_age'] < 100 and loser_chars['avg_age'] > 150:
            suggestions['recommended_changes'].append(
                f"Reduce maximum token age from 720h to {winner_chars['max_age']:.0f}h"
            )
            suggestions['new_thresholds']['max_age_hours'] = winner_chars['max_age']
        
        # Market cap insight
        winner_mcap = self._safe_mean([t['entry_market_cap'] for t in winners if t['entry_market_cap'] > 0])
        loser_mcap = self._safe_mean([t['entry_market_cap'] for t in losers if t['entry_market_cap'] > 0])
        if winner_mcap < 5000000 and loser_mcap > 10000000:
            suggestions['recommended_changes'].append(
                f"Focus on smaller market cap tokens (<$5M instead of <$20M)"
            )
            suggestions['new_thresholds']['max_market_cap'] = 5000000
        
        return suggestions
    
    def _safe_mean(self, values: List) -> float:
        """Calculate mean safely"""
        clean_values = [v for v in values if v is not None and v > 0]
        return statistics.mean(clean_values) if clean_values else 0
    
    def _safe_median(self, values: List) -> float:
        """Calculate median safely"""
        clean_values = [v for v in values if v is not None and v > 0]
        return statistics.median(clean_values) if clean_values else 0
    
    def _count_risk_levels(self, tokens: List[Dict]) -> Dict:
        """Count risk level distribution"""
        risk_counts = {'low': 0, 'medium': 0, 'high': 0, 'unknown': 0}
        for token in tokens:
            risk = token.get('risk_level', 'unknown')
            if risk in risk_counts:
                risk_counts[risk] += 1
            else:
                risk_counts['unknown'] += 1
        return risk_counts
    
    def _count_trends(self, tokens: List[Dict]) -> Dict:
        """Count trend distribution"""
        trend_counts = {}
        for token in tokens:
            trend = token.get('entry_trend', 'unknown')
            trend_counts[trend] = trend_counts.get(trend, 0) + 1
        return trend_counts
    
    def _calculate_avg_liquidity_change(self, tokens: List[Dict]) -> float:
        """Calculate average liquidity change"""
        changes = []
        for token in tokens:
            if token['entry_liquidity'] > 0:
                change = ((token['latest_liquidity'] - token['entry_liquidity']) / token['entry_liquidity']) * 100
                changes.append(change)
        return statistics.mean(changes) if changes else 0
    
    def _calculate_avg_volume_change(self, tokens: List[Dict]) -> float:
        """Calculate average volume change"""
        changes = []
        for token in tokens:
            if token['entry_volume'] > 0:
                change = ((token['latest_volume'] - token['entry_volume']) / token['entry_volume']) * 100
                changes.append(change)
        return statistics.mean(changes) if changes else 0

# Global analyzer instance
pattern_analyzer = PatternAnalyzer()