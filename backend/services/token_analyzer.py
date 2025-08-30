import time
import threading
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from .dextools_service import DEXToolsService

class TokenAnalyzer:
    def __init__(self):
        self.dextools = DEXToolsService()
        self.analysis_results = []
        self.rejected_tokens = []
        self.is_running = False
        self.current_analysis = None
        self.analysis_thread = None
        
        # Analysis criteria
        self.criteria = {
            'max_market_cap': 1500000,  # $1.5M
            'min_liquidity': 10000,     # $10K minimum liquidity
            'min_volume_24h': 5000,     # $5K minimum 24h volume
            'min_dext_score': 70,       # Minimum security score
            'max_age_hours': 168,       # Max 7 days old (168 hours)
            'min_holders': 50,          # Minimum number of holders
            'min_price_change_24h': 0,  # Must be stable or growing (>= 0%) in 24h
            'min_price_change_1h': -5,  # Allow small 1h drops but not more than -5%
            'min_price_change_5m': -10, # Allow moderate 5m drops but not more than -10%
            'max_price_drop_24h': -20,  # Reject if 24h drop > 20%
            'max_price_drop_1h': -15,   # Reject if 1h drop > 15%
            'max_price_drop_5m': -20    # Reject if 5m drop > 20%
        }

    def start_background_analysis(self):
        """Start the background analysis process"""
        if self.is_running:
            return
        
        self.is_running = True
        self.analysis_thread = threading.Thread(target=self._analysis_loop, daemon=True)
        self.analysis_thread.start()
        print("🤖 Token analyzer started in background")

    def stop_background_analysis(self):
        """Stop the background analysis process"""
        self.is_running = False
        if self.analysis_thread:
            self.analysis_thread.join(timeout=5)
        print("🛑 Token analyzer stopped")

    def _analysis_loop(self):
        """Main analysis loop that runs every 3 minutes"""
        while self.is_running:
            try:
                self._analyze_next_token()
                # Sleep for 3 minutes (180 seconds)
                for _ in range(180):
                    if not self.is_running:
                        break
                    time.sleep(1)
            except Exception as e:
                print(f"❌ Analysis error: {e}")
                time.sleep(30)  # Wait 30 seconds on error

    def _analyze_next_token(self):
        """Analyze the next token from hot pools"""
        try:
            # Get fresh hot pools data
            pools = self.dextools.get_hot_pools(30)
            if not pools:
                print("📊 No pools available for analysis")
                return

            # Reverse to match frontend display order (30, 29, 28... down to 1)
            pools.reverse()

            # Find a token we haven't analyzed recently, in display order (30, 29, 28...)
            for pool in pools:
                if not pool.get('mainToken', {}).get('address'):
                    continue
                
                token_address = pool['mainToken']['address']
                
                # Skip if analyzed in the last hour
                if self._was_recently_analyzed(token_address):
                    continue
                
                # Perform analysis
                rank = pool.get('rank', '?')
                symbol = pool.get('mainToken', {}).get('symbol', 'Unknown')
                print(f"🔍 Analyzing rank #{rank} token: {symbol} ({token_address[:8]}...)")
                self._analyze_token(token_address, pool)
                break
            else:
                print("🔄 All tokens recently analyzed, waiting for next cycle")

        except Exception as e:
            print(f"❌ Error in analysis cycle: {e}")

    def _was_recently_analyzed(self, token_address: str) -> bool:
        """Check if token was analyzed in the last hour"""
        one_hour_ago = datetime.now() - timedelta(hours=1)
        
        # Check both approved and rejected lists
        all_analyses = self.analysis_results + self.rejected_tokens
        
        for analysis in all_analyses:
            if (analysis.get('token_address') == token_address and 
                datetime.fromisoformat(analysis.get('analyzed_at', '2020-01-01T00:00:00')) > one_hour_ago):
                return True
        return False

    def _analyze_token(self, token_address: str, pool: Dict):
        """Perform comprehensive token analysis"""
        self.current_analysis = {
            'token_address': token_address,
            'pool_info': pool,
            'status': 'analyzing',
            'started_at': datetime.now().isoformat()
        }
        
        print(f"🔍 Analyzing token: {token_address}")
        
        try:
            # Get comprehensive analysis
            analysis = self.dextools.get_complete_token_analysis(token_address)
            
            if not analysis.get('success'):
                self._reject_token(token_address, pool, "Failed to fetch token data")
                return

            # Extract data for evaluation
            token_data = self._extract_token_data(analysis, pool)
            
            # Evaluate token against criteria
            evaluation = self._evaluate_token(token_data)
            
            if evaluation['approved']:
                self._approve_token(token_data, evaluation)
            else:
                self._reject_token(token_address, pool, evaluation['rejection_reasons'])
                
        except Exception as e:
            self._reject_token(token_address, pool, f"Analysis error: {str(e)}")
        finally:
            self.current_analysis = None

    def _extract_token_data(self, analysis: Dict, pool: Dict) -> Dict:
        """Extract relevant data from API response"""
        info = analysis.get('info', {}).get('data', {}) if analysis.get('info', {}).get('statusCode') == 200 else {}
        price = analysis.get('price', {}).get('data', {}) if analysis.get('price', {}).get('statusCode') == 200 else {}
        score = analysis.get('score', {}).get('data', {}) if analysis.get('score', {}).get('statusCode') == 200 else {}
        metrics = analysis.get('metrics', {}).get('data', {}) if analysis.get('metrics', {}).get('statusCode') == 200 else {}
        
        # Calculate age
        creation_time = info.get('creationTime') or pool.get('creationTime')
        age_hours = 0
        if creation_time:
            try:
                created = datetime.fromisoformat(creation_time.replace('Z', '+00:00'))
                age_hours = (datetime.now().replace(tzinfo=created.tzinfo) - created).total_seconds() / 3600
            except:
                pass

        return {
            'token_address': analysis['token_address'],
            'name': info.get('name', 'Unknown'),
            'symbol': info.get('symbol', 'Unknown'),
            'creation_time': creation_time,
            'age_hours': age_hours,
            'market_cap': metrics.get('mcap', 0),
            'liquidity': metrics.get('liquidity_usd', 0),
            'volume_24h': metrics.get('volume_24h_usd', 0),
            'volume_1h': metrics.get('volume_1h_usd', 0),
            'dext_score': score.get('dextScore', {}).get('total', 0),
            'upvotes': score.get('votes', {}).get('upvotes', 0),
            'downvotes': score.get('votes', {}).get('downvotes', 0),
            'holders_count': metrics.get('holders_count', 0),
            'price': price.get('price', 0),
            'price_change_24h': price.get('variation24h', 0),
            'price_change_1h': price.get('variation1h', 0),
            'price_change_5m': price.get('variation5m', 0),
            'pool_rank': pool.get('rank', 999),
            'exchange': pool.get('exchange', {}).get('name', 'Unknown'),
            'analyzed_at': datetime.now().isoformat()
        }

    def _evaluate_token(self, token_data: Dict) -> Dict:
        """Evaluate token against safety criteria"""
        reasons = []
        warnings = []
        
        # Market cap check
        if token_data['market_cap'] and token_data['market_cap'] > self.criteria['max_market_cap']:
            reasons.append(f"Market cap too high: ${token_data['market_cap']:,.0f} > ${self.criteria['max_market_cap']:,.0f}")
        
        # Liquidity check
        if token_data['liquidity'] is not None and token_data['liquidity'] < self.criteria['min_liquidity']:
            reasons.append(f"Low liquidity: ${token_data['liquidity']:,.0f} < ${self.criteria['min_liquidity']:,.0f}")
        
        # Volume check
        if token_data['volume_24h'] is not None and token_data['volume_24h'] < self.criteria['min_volume_24h']:
            reasons.append(f"Low 24h volume: ${token_data['volume_24h']:,.0f} < ${self.criteria['min_volume_24h']:,.0f}")
        
        # Security score check
        if token_data['dext_score'] is not None and token_data['dext_score'] < self.criteria['min_dext_score']:
            reasons.append(f"Low security score: {token_data['dext_score']} < {self.criteria['min_dext_score']}")
        
        # Age check (too new can be risky)
        if token_data['age_hours'] is not None:
            if token_data['age_hours'] > self.criteria['max_age_hours']:
                reasons.append(f"Token too old: {token_data['age_hours']:.1f}h > {self.criteria['max_age_hours']}h")
            elif token_data['age_hours'] < 1:
                warnings.append("Very new token (< 1 hour old)")
        
        # Holder count check
        if token_data['holders_count'] is not None and token_data['holders_count'] < self.criteria['min_holders']:
            reasons.append(f"Too few holders: {token_data['holders_count']} < {self.criteria['min_holders']}")
        
        # Critical price trend checks (rejection criteria)
        if token_data['price_change_24h'] is not None and token_data['price_change_24h'] < self.criteria['max_price_drop_24h']:
            reasons.append(f"Large 24h price drop: {token_data['price_change_24h']:.1f}% < {self.criteria['max_price_drop_24h']}%")
        
        if token_data['price_change_1h'] is not None and token_data['price_change_1h'] < self.criteria['max_price_drop_1h']:
            reasons.append(f"Large 1h price drop: {token_data['price_change_1h']:.1f}% < {self.criteria['max_price_drop_1h']}%")
        
        # Growth/stability requirements
        if token_data['price_change_24h'] is not None and token_data['price_change_24h'] < self.criteria['min_price_change_24h']:
            reasons.append(f"24h declining trend: {token_data['price_change_24h']:.1f}% < {self.criteria['min_price_change_24h']}% (must be stable or growing)")
        
        if token_data['price_change_1h'] is not None and token_data['price_change_1h'] < self.criteria['min_price_change_1h']:
            reasons.append(f"1h declining trend: {token_data['price_change_1h']:.1f}% < {self.criteria['min_price_change_1h']}%")
        
        # 5-minute trend check (critical drop rejection)
        if token_data['price_change_5m'] is not None and token_data['price_change_5m'] < self.criteria['max_price_drop_5m']:
            reasons.append(f"Large 5m price drop: {token_data['price_change_5m']:.1f}% < {self.criteria['max_price_drop_5m']}%")
        
        if token_data['price_change_5m'] is not None and token_data['price_change_5m'] < self.criteria['min_price_change_5m']:
            reasons.append(f"5m declining trend: {token_data['price_change_5m']:.1f}% < {self.criteria['min_price_change_5m']}%")
        
        # Warnings for moderate drops
        if token_data['price_change_24h'] is not None and -10 <= token_data['price_change_24h'] < 0:
            warnings.append(f"Moderate 24h decline: {token_data['price_change_24h']:.1f}%")
        
        if token_data['price_change_1h'] is not None and -5 <= token_data['price_change_1h'] < 0:
            warnings.append(f"Moderate 1h decline: {token_data['price_change_1h']:.1f}%")
        
        if token_data['price_change_5m'] is not None and -5 <= token_data['price_change_5m'] < 0:
            warnings.append(f"Moderate 5m decline: {token_data['price_change_5m']:.1f}%")
        
        # Vote analysis
        if token_data['downvotes'] > token_data['upvotes'] * 2:
            warnings.append(f"Negative sentiment: {token_data['downvotes']} downvotes vs {token_data['upvotes']} upvotes")

        return {
            'approved': len(reasons) == 0,
            'rejection_reasons': reasons,
            'warnings': warnings,
            'score': self._calculate_opportunity_score(token_data, warnings)
        }

    def _calculate_opportunity_score(self, token_data: Dict, warnings: List[str]) -> float:
        """Calculate an opportunity score (0-100)"""
        score = 50  # Base score
        
        # Positive factors
        score += min(token_data['dext_score'] / 2, 40)  # Max +40 for perfect security score
        score += min(token_data['volume_24h'] / 10000, 10)  # Max +10 for high volume
        score += min(token_data['pool_rank'] / 30 * 10, 10)  # Max +10 for good ranking
        
        # Recent performance bonus (growth trend)
        if token_data['price_change_5m'] is not None and token_data['price_change_5m'] > 0:
            score += min(token_data['price_change_5m'] / 2, 10)  # Max +10 for 5m growth
        
        if token_data['price_change_1h'] is not None and token_data['price_change_1h'] > 0:
            score += min(token_data['price_change_1h'] / 2, 10)  # Max +10 for 1h growth
            
        if token_data['price_change_24h'] is not None and token_data['price_change_24h'] > 0:
            score += min(token_data['price_change_24h'] / 5, 15)  # Max +15 for 24h growth
        
        # Strong growth bonuses
        if token_data['price_change_5m'] is not None and token_data['price_change_5m'] > 10:
            score += 5  # Bonus for strong 5m growth
            
        if token_data['price_change_1h'] is not None and token_data['price_change_1h'] > 10:
            score += 5  # Bonus for strong 1h growth
        
        # Deduct for warnings
        score -= len(warnings) * 3
        
        return max(0, min(100, score))

    def _approve_token(self, token_data: Dict, evaluation: Dict):
        """Add token to approved list"""
        result = {
            **token_data,
            'evaluation': evaluation,
            'status': 'approved'
        }
        
        # Keep only top 10 approved tokens
        self.analysis_results.append(result)
        self.analysis_results.sort(key=lambda x: x['evaluation']['score'], reverse=True)
        self.analysis_results = self.analysis_results[:10]
        
        print(f"✅ Token approved: {token_data['symbol']} (Score: {evaluation['score']:.1f})")

    def _reject_token(self, token_address: str, pool: Dict, reasons):
        """Add token to rejected list"""
        if isinstance(reasons, str):
            reasons = [reasons]
        
        result = {
            'token_address': token_address,
            'name': pool.get('mainToken', {}).get('name', 'Unknown'),
            'symbol': pool.get('mainToken', {}).get('symbol', 'Unknown'),
            'pool_rank': pool.get('rank', 999),
            'rejection_reasons': reasons,
            'analyzed_at': datetime.now().isoformat(),
            'status': 'rejected'
        }
        
        # Keep only last 20 rejected tokens
        self.rejected_tokens.append(result)
        self.rejected_tokens = self.rejected_tokens[-20:]
        
        print(f"❌ Token rejected: {result['symbol']} - {'; '.join(reasons)}")

    def get_analysis_status(self) -> Dict:
        """Get current analysis status"""
        return {
            'is_running': self.is_running,
            'current_analysis': self.current_analysis,
            'approved_count': len(self.analysis_results),
            'rejected_count': len(self.rejected_tokens),
            'criteria': self.criteria
        }

    def get_approved_tokens(self) -> List[Dict]:
        """Get list of approved tokens"""
        return self.analysis_results.copy()

    def get_rejected_tokens(self) -> List[Dict]:
        """Get list of rejected tokens"""
        return self.rejected_tokens.copy()

    def update_criteria(self, new_criteria: Dict):
        """Update analysis criteria"""
        self.criteria.update(new_criteria)
        print(f"📋 Updated analysis criteria: {new_criteria}")