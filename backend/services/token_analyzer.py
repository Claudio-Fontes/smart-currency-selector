import time
import threading
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from .dextools_service import DEXToolsService

# Optional database import - continue without DB if unavailable
try:
    from ..database import token_repo
    DB_AVAILABLE = True
except Exception as e:
    print(f"⚠️  Database not available: {e}")
    token_repo = None
    DB_AVAILABLE = False

# Optional Telegram import - continue without Telegram if unavailable
try:
    from .telegram_notifier import telegram_notifier
    TELEGRAM_AVAILABLE = True
except Exception as e:
    print(f"⚠️  Telegram notifications not available: {e}")
    telegram_notifier = None
    TELEGRAM_AVAILABLE = False

class TokenAnalyzer:
    def __init__(self):
        self.dextools = DEXToolsService()
        self.analysis_results = []
        self.rejected_tokens = []
        self.is_running = False
        self.current_analysis = None
        self.analysis_thread = None
        
        # Analysis criteria - OPTIMIZED based on pattern analysis
        self.criteria = {
            # Market cap & basic filters
            'max_market_cap': 3000000,   # $3M - reduced from $20M based on winners analysis
            'min_liquidity': 50000,      # $50K - increased from $10K (winners had $166K avg)
            'optimal_liquidity_min': 100000,  # $100K - optimal range start
            'optimal_liquidity_max': 200000,  # $200K - optimal range end
            'min_volume_24h': 10000,     # $10K - increased from $5K
            'max_initial_volume_24h': 2000000,  # $2M - NEW: prevent pump & dump
            
            # Volume/Liquidity ratio checks - NEW CRITICAL CRITERIA
            'max_volume_liquidity_ratio': 8.0,   # NEW: Volume should not exceed 8x liquidity
            'warning_volume_liquidity_ratio': 10.0,  # NEW: Strong warning if >10x
            'optimal_volume_liquidity_ratio_min': 0.5,  # NEW: Optimal range 0.5-5.0
            'optimal_volume_liquidity_ratio_max': 5.0,
            
            # Security & holders
            'min_dext_score': 85,        # Increased from 70 based on winners (min was 85)
            'min_holders': 100,          # Increased from 50
            'max_holders_if_dropping': 2000,  # NEW: Too many holders + price drop = red flag
            
            # Age
            'max_age_hours': 936,        # 39 days - increased by 30% to allow more tokens
            
            # Price movement tolerances
            'min_price_change_24h': -5,  # Allow small decline (was 0)
            'min_price_change_1h': -5,   # Keep same
            'min_price_change_5m': -10,  # Keep same
            'max_price_drop_24h': -15,   # Tightened from -20%
            'max_price_drop_1h': -10,    # Tightened from -15%
            'max_price_drop_5m': -15     # Tightened from -20%
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
        """Main analysis loop that runs every 30 seconds for faster processing"""
        while self.is_running:
            try:
                self._analyze_next_token()
                # Sleep for 30 seconds (much faster processing)
                for _ in range(30):
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

            # Analyze multiple tokens per cycle for faster processing
            tokens_analyzed = 0
            max_per_cycle = 5  # Process up to 5 tokens per cycle
            
            for pool in pools:
                if tokens_analyzed >= max_per_cycle:
                    break
                    
                if not pool.get('mainToken', {}).get('address'):
                    continue
                
                token_address = pool['mainToken']['address']
                
                # Skip if analyzed recently (now 5 minutes instead of 1 hour)
                if self._was_recently_analyzed(token_address):
                    continue
                
                # Perform analysis
                rank = pool.get('rank', '?')
                symbol = pool.get('mainToken', {}).get('symbol', 'Unknown')
                print(f"🔍 Analyzing rank #{rank} token: {symbol} ({token_address[:8]}...)")
                self._analyze_token(token_address, pool)
                tokens_analyzed += 1
                
            if tokens_analyzed == 0:
                print("🔄 All recent tokens analyzed, waiting for new tokens")
            else:
                print(f"✅ Processed {tokens_analyzed} tokens this cycle")

        except Exception as e:
            print(f"❌ Error in analysis cycle: {e}")

    def _was_recently_analyzed(self, token_address: str) -> bool:
        """Check if token was analyzed recently (reduced cooldown for faster processing)"""
        # Reduced cooldown to 5 minutes for much faster processing
        five_minutes_ago = datetime.now() - timedelta(minutes=5)
        
        # Check both approved and rejected lists
        all_analyses = self.analysis_results + self.rejected_tokens
        
        for analysis in all_analyses:
            if (analysis.get('token_address') == token_address and 
                datetime.fromisoformat(analysis.get('analyzed_at', '2020-01-01T00:00:00')) > five_minutes_ago):
                return True
        return False

    def _calculate_pool_age(self, creation_time: str) -> Optional[float]:
        """Calculate pool age in hours"""
        if not creation_time:
            return None
        try:
            created = datetime.fromisoformat(creation_time.replace('Z', '+00:00'))
            return (datetime.now().replace(tzinfo=created.tzinfo) - created).total_seconds() / 3600
        except:
            return None

    def _calculate_token_age(self, creation_time: str) -> Optional[float]:
        """Calculate token age in hours"""
        if not creation_time:
            return None
        try:
            created = datetime.fromisoformat(creation_time.replace('Z', '+00:00'))
            return (datetime.now().replace(tzinfo=created.tzinfo) - created).total_seconds() / 3600
        except:
            return None

    def _analyze_token(self, token_address: str, pool: Dict):
        """Perform optimized token analysis with early rejection"""
        start_time = datetime.now()
        self.current_analysis = {
            'token_address': token_address,
            'pool_info': pool,
            'status': 'analyzing',
            'started_at': start_time.isoformat()
        }
        
        print(f"🔍 Analyzing token: {token_address}")
        
        try:
            # PHASE 1: Quick basic checks (no API calls needed)
            pool_age_hours = self._calculate_pool_age(pool.get('creationTime'))
            if pool_age_hours is not None and pool_age_hours > self.criteria['max_age_hours']:
                self._reject_token(token_address, pool, f"Pool too old: {pool_age_hours:.1f}h > {self.criteria['max_age_hours']}h", "age_check")
                return
            
            # PHASE 2: Basic token info (lightweight API call)
            basic_info = self.dextools.get_token_info(token_address)
            if not basic_info.get('success') or basic_info.get('statusCode') != 200:
                self._reject_token(token_address, pool, "Failed to fetch basic token info", "api_error")
                return
            
            info_data = basic_info.get('data', {})
            creation_time = info_data.get('creationTime')
            if creation_time:
                token_age_hours = self._calculate_token_age(creation_time)
                if token_age_hours is not None and token_age_hours > self.criteria['max_age_hours']:
                    self._reject_token(token_address, pool, f"Token too old: {token_age_hours:.1f}h > {self.criteria['max_age_hours']}h", "age_check")
                    return
            
            # PHASE 3: Price data (quick check)
            price_data = self.dextools.get_token_price(token_address)
            if not price_data.get('success') or price_data.get('statusCode') != 200:
                self._reject_token(token_address, pool, "Failed to fetch price data", "api_error")
                return
            
            price_info = price_data.get('data', {})
            
            # Early rejection on critical price drops
            price_24h = price_info.get('variation24h')
            if price_24h is not None and price_24h < self.criteria['max_price_drop_24h']:
                self._reject_token(token_address, pool, f"Large 24h drop: {price_24h:.1f}% < {self.criteria['max_price_drop_24h']}%", "price_drop")
                return
            
            price_1h = price_info.get('variation1h')
            if price_1h is not None and price_1h < self.criteria['max_price_drop_1h']:
                self._reject_token(token_address, pool, f"Large 1h drop: {price_1h:.1f}% < {self.criteria['max_price_drop_1h']}%", "price_drop")
                return
            
            # Check growth requirements early
            if price_24h is not None and price_24h < self.criteria['min_price_change_24h']:
                self._reject_token(token_address, pool, f"24h declining: {price_24h:.1f}% < {self.criteria['min_price_change_24h']}%", "declining_trend")
                return
            
            # PHASE 4: Metrics data (more expensive but still quick)
            metrics_data = self.dextools.get_token_metrics(token_address)
            if not metrics_data.get('success') or metrics_data.get('statusCode') != 200:
                self._reject_token(token_address, pool, "Failed to fetch metrics data", "api_error")
                return
            
            metrics_info = metrics_data.get('data', {})
            
            # Early rejection on market cap (most important filter)
            market_cap = metrics_info.get('mcap', 0)
            if market_cap and market_cap > self.criteria['max_market_cap']:
                self._reject_token(token_address, pool, f"Market cap too high: ${market_cap:,.0f} > ${self.criteria['max_market_cap']:,.0f}", "market_cap")
                return
            
            # Early rejection on liquidity
            liquidity = metrics_info.get('liquidity_usd', 0)
            if liquidity < self.criteria['min_liquidity']:
                self._reject_token(token_address, pool, f"Low liquidity: ${liquidity:,.0f} < ${self.criteria['min_liquidity']:,.0f}", "liquidity")
                return
            
            # Early rejection on volume
            volume_24h = metrics_info.get('volume_24h_usd', 0)
            if volume_24h < self.criteria['min_volume_24h']:
                self._reject_token(token_address, pool, f"Low volume: ${volume_24h:,.0f} < ${self.criteria['min_volume_24h']:,.0f}", "volume")
                return
            
            # NEW: Check volume/liquidity ratio - CRITICAL for avoiding pump & dump
            if liquidity > 0:
                volume_liquidity_ratio = volume_24h / liquidity
                
                # Hard rejection if ratio is too high (likely pump & dump)
                if volume_liquidity_ratio > self.criteria['warning_volume_liquidity_ratio']:
                    self._reject_token(token_address, pool, 
                        f"🚨 PUMP WARNING: Volume/Liquidity ratio too high: {volume_liquidity_ratio:.1f}x (max {self.criteria['warning_volume_liquidity_ratio']}x)", 
                        "pump_warning")
                    return
                
                # Soft rejection if ratio is above max but below warning
                if volume_liquidity_ratio > self.criteria['max_volume_liquidity_ratio']:
                    self._reject_token(token_address, pool, 
                        f"High Volume/Liquidity ratio: {volume_liquidity_ratio:.1f}x (max {self.criteria['max_volume_liquidity_ratio']}x)", 
                        "high_volume_ratio")
                    return
                
                # Log if in optimal range (for tracking)
                if (self.criteria['optimal_volume_liquidity_ratio_min'] <= volume_liquidity_ratio <= 
                    self.criteria['optimal_volume_liquidity_ratio_max']):
                    print(f"✅ Optimal V/L ratio: {volume_liquidity_ratio:.2f}x")
            
            # NEW: Check for excessive initial volume (pump indicator)
            if volume_24h > self.criteria['max_initial_volume_24h']:
                self._reject_token(token_address, pool, 
                    f"Excessive initial volume: ${volume_24h:,.0f} > ${self.criteria['max_initial_volume_24h']:,.0f} (pump risk)", 
                    "excessive_volume")
                return
            
            # Early rejection on holders
            holders = metrics_info.get('holders_count', 0)
            if holders < self.criteria['min_holders']:
                self._reject_token(token_address, pool, f"Too few holders: {holders} < {self.criteria['min_holders']}", "holders")
                return
            
            # NEW: Check for red flag - many holders but price dropping (bad distribution)
            if holders > self.criteria['max_holders_if_dropping'] and price_24h is not None and price_24h < -5:
                self._reject_token(token_address, pool, 
                    f"🚨 Distribution warning: {holders} holders but price dropping {price_24h:.1f}% (bad distribution)", 
                    "bad_distribution")
                return
            
            # PHASE 5: Security score (only if passed all basic checks)
            print(f"✅ Token {token_address[:8]}... passed basic checks, checking security...")
            score_data = self.dextools.get_token_score(token_address)
            
            dext_score = 0
            if score_data.get('success') and score_data.get('statusCode') == 200:
                score_info = score_data.get('data', {})
                dext_score = score_info.get('dextScore', {}).get('total', 0)
            
            if dext_score < self.criteria['min_dext_score']:
                self._reject_token(token_address, pool, f"Low security score: {dext_score} < {self.criteria['min_dext_score']}", "security_score")
                return
            
            # PHASE 6: Full analysis (only for tokens that passed all filters)
            print(f"🎯 Token {token_address[:8]}... passed all filters, performing full analysis...")
            analysis = self.dextools.get_complete_token_analysis(token_address)
            
            if not analysis.get('success'):
                self._reject_token(token_address, pool, "Failed to fetch complete analysis", "api_error")
                return

            # Extract data for final evaluation
            token_data = self._extract_token_data(analysis, pool)
            
            # Final evaluation (should mostly pass at this point)
            evaluation = self._evaluate_token(token_data)
            
            elapsed_time = (datetime.now() - start_time).total_seconds()
            print(f"⏱️ Analysis completed in {elapsed_time:.2f}s")
            
            if evaluation['approved']:
                self._approve_token(token_data, evaluation)
            else:
                self._reject_token(token_address, pool, evaluation['rejection_reasons'], "final_evaluation")
                
        except Exception as e:
            self._reject_token(token_address, pool, f"Analysis error: {str(e)}", "exception")
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
        """Calculate an opportunity score (0-100) - OPTIMIZED based on pattern analysis"""
        score = 50  # Base score
        
        # Security score (critical factor)
        score += min(token_data['dext_score'] / 2, 40)  # Max +40 for perfect security score
        
        # NEW: Volume/Liquidity ratio bonus (most important pattern discovered)
        if token_data['liquidity'] > 0 and token_data['volume_24h'] > 0:
            vol_liq_ratio = token_data['volume_24h'] / token_data['liquidity']
            
            # Optimal ratio bonus (0.5 to 5.0)
            if 0.5 <= vol_liq_ratio <= 5.0:
                score += 20  # Big bonus for optimal ratio
                if 1.0 <= vol_liq_ratio <= 3.0:
                    score += 10  # Extra bonus for perfect ratio
            elif vol_liq_ratio < 0.5:
                score -= 10  # Too low volume relative to liquidity
            elif vol_liq_ratio > 8.0:
                score -= 30  # High pump risk
        
        # NEW: Liquidity in optimal range bonus
        liquidity = token_data.get('liquidity', 0)
        if 100000 <= liquidity <= 200000:
            score += 15  # Optimal liquidity range
        elif 50000 <= liquidity < 100000:
            score += 5   # Acceptable liquidity
        elif liquidity > 500000:
            score -= 5   # Too high might be artificial
        
        # Holder count bonus (adjusted based on patterns)
        holders = token_data.get('holders_count', 0)
        if 500 <= holders <= 1500:
            score += 10  # Optimal holder range
        elif holders > 2000:
            # Check if price is also positive
            if token_data.get('price_change_24h', 0) > 0:
                score += 5
            else:
                score -= 10  # Many holders but price dropping = bad
        
        # Pool ranking (less important now)
        if token_data['pool_rank'] <= 10:
            score += 5  # Top 10 pool
        
        # Recent performance (keep but reduced weight)
        if token_data['price_change_24h'] is not None and token_data['price_change_24h'] > 0:
            score += min(token_data['price_change_24h'] / 10, 10)  # Max +10 for 24h growth
        
        if token_data['price_change_1h'] is not None and token_data['price_change_1h'] > 5:
            score += 5  # Bonus for strong 1h growth
        
        # Market cap bonus (prefer smaller caps based on analysis)
        market_cap = token_data.get('market_cap', 0)
        if 0 < market_cap <= 1000000:
            score += 10  # Under $1M market cap
        elif market_cap > 5000000:
            score -= 10  # Too large
        
        # Deduct for warnings
        score -= len(warnings) * 3
        
        return max(0, min(100, score))

    def _approve_token(self, token_data: Dict, evaluation: Dict):
        """Add token to approved list and save to database"""
        result = {
            **token_data,
            'evaluation': evaluation,
            'status': 'approved'
        }
        
        # Keep only top 10 approved tokens
        self.analysis_results.append(result)
        self.analysis_results.sort(key=lambda x: x['evaluation']['score'], reverse=True)
        self.analysis_results = self.analysis_results[:10]
        
        # Save to database (optional - continue if DB unavailable)
        db_success = False
        if DB_AVAILABLE and token_repo:
            try:
                db_data = self._prepare_token_for_database(token_data, evaluation)
                db_success = token_repo.save_suggested_token(db_data)
                if db_success:
                    print(f"✅ Token approved and saved to DB: {token_data['symbol']} (Score: {evaluation['score']:.1f})")
                    
                    # Auto-buy if score is high enough
                    if evaluation['score'] >= 80:
                        try:
                            # Import buy_service
                            import sys
                            from pathlib import Path
                            sys.path.insert(0, str(Path(__file__).parent.parent.parent))
                            from trade.services.buy_service import buy_service
                            
                            # Prepare token data for buy service
                            buy_token_data = {
                                'token_address': token_data['token_address'],
                                'token_symbol': token_data.get('symbol', 'Unknown'),
                                'token_name': token_data.get('name', 'Unknown'),
                                'price_usd': token_data.get('price', 0),
                                'market_cap': token_data.get('market_cap', 0),
                                'volume_24h': token_data.get('volume_24h', 0),
                                'price_change_24h': token_data.get('price_change_24h', 0),
                                'buy_reason': f'AUTO_BUY_SCORE_{evaluation["score"]:.0f}'
                            }
                            
                            # Execute buy
                            buy_result = buy_service.execute_buy(buy_token_data)
                            
                            if buy_result:
                                print(f"🚀 AUTO-BUY EXECUTED! Trade ID: {buy_result['trade_id']}, TX: {buy_result['transaction_hash'][:20]}...")
                            else:
                                print(f"🔍 Auto-buy skipped (already have position or trading disabled)")
                                
                        except Exception as e:
                            print(f"⚠️ Auto-buy error: {str(e)[:100]}...")
                else:
                    print(f"✅ Token approved: {token_data['symbol']} (Score: {evaluation['score']:.1f}) - DB save failed")
            except Exception as e:
                print(f"✅ Token approved: {token_data['symbol']} (Score: {evaluation['score']:.1f}) - DB error: {str(e)[:50]}...")
        else:
            print(f"✅ Token approved: {token_data['symbol']} (Score: {evaluation['score']:.1f}) - DB not available")
        
        # Send Telegram notification (optional - continue if Telegram unavailable)
        if TELEGRAM_AVAILABLE and telegram_notifier:
            try:
                telegram_success = telegram_notifier.send_token_suggestion(token_data, evaluation)
                if telegram_success:
                    print(f"📱 Telegram notification sent for {token_data['symbol']}")
                else:
                    print(f"📱 Telegram notification failed for {token_data['symbol']}")
            except Exception as e:
                print(f"📱 Telegram error for {token_data['symbol']}: {str(e)[:50]}...")
        else:
            print(f"📱 Telegram notifications not configured")
            
    def _prepare_token_for_database(self, token_data: Dict, evaluation: Dict) -> Dict:
        """Prepare token data for database storage"""
        return {
            'token_address': token_data['token_address'],
            'name': token_data.get('name', 'Unknown'),
            'symbol': token_data.get('symbol', 'Unknown'),
            'chain': 'solana',  # Currently only supporting Solana
            
            # Price metrics
            'price': token_data.get('price'),
            'price_change_24h': token_data.get('price_change_24h'),
            'volume_24h': token_data.get('volume_24h'),
            'liquidity': token_data.get('liquidity'),
            'market_cap': token_data.get('market_cap'),
            
            # Security metrics
            'pool_score': token_data.get('dext_score'),
            'liquidity_locked': None,  # Not available in current data
            'is_audited': None,  # Not available in current data
            'honeypot_risk': None,  # Not available in current data
            
            # Holders analysis
            'holder_count': token_data.get('holders_count'),
            'top_10_holders_percentage': None,  # Not available in current data
            'concentration_risk': self._assess_concentration_risk(token_data.get('holders_count')),
            
            # Price trend analysis
            'price_trend': self._assess_price_trend(token_data),
            'trend_confidence': evaluation.get('score'),
            
            # Pool information
            'pool_address': None,  # Would need additional data
            'pool_created_at': token_data.get('creation_time'),
            'dex_name': token_data.get('exchange', 'Unknown'),
            
            # Analysis metadata
            'suggestion_reason': f"AI Analysis: Score {evaluation.get('score', 0):.1f}/100",
            'analysis_score': evaluation.get('score'),
            'risk_level': self._assess_risk_level(evaluation.get('score', 0), evaluation.get('warnings', [])),
            
            # Additional context
            'age_hours': token_data.get('age_hours'),
            'upvotes': token_data.get('upvotes', 0),
            'downvotes': token_data.get('downvotes', 0),
            'pool_rank': token_data.get('pool_rank')
        }
    
    def _assess_concentration_risk(self, holders_count: Optional[int]) -> str:
        """Assess concentration risk based on holder count"""
        if holders_count is None:
            return 'unknown'
        elif holders_count < 100:
            return 'high'
        elif holders_count < 500:
            return 'medium'
        else:
            return 'low'
    
    def _assess_price_trend(self, token_data: Dict) -> str:
        """Assess overall price trend"""
        price_24h = token_data.get('price_change_24h', 0)
        price_1h = token_data.get('price_change_1h', 0)
        price_5m = token_data.get('price_change_5m', 0)
        
        if price_24h > 10 and price_1h > 0:
            return 'strong_bullish'
        elif price_24h > 0 and price_1h >= 0:
            return 'bullish'
        elif price_24h >= 0 and price_1h > -5:
            return 'neutral'
        elif price_24h > -10:
            return 'bearish'
        else:
            return 'strong_bearish'
    
    def _assess_risk_level(self, score: float, warnings: List[str]) -> str:
        """Assess overall risk level"""
        if score >= 80 and len(warnings) == 0:
            return 'low'
        elif score >= 60 and len(warnings) <= 2:
            return 'medium'
        else:
            return 'high'

    def _reject_token(self, token_address: str, pool: Dict, reasons, category: str = "unknown"):
        """Add token to rejected list with rejection category tracking"""
        if isinstance(reasons, str):
            reasons = [reasons]
        
        result = {
            'token_address': token_address,
            'name': pool.get('mainToken', {}).get('name', 'Unknown'),
            'symbol': pool.get('mainToken', {}).get('symbol', 'Unknown'),
            'pool_rank': pool.get('rank', 999),
            'rejection_reasons': reasons,
            'rejection_category': category,
            'analyzed_at': datetime.now().isoformat(),
            'status': 'rejected'
        }
        
        # Keep only last 20 rejected tokens
        self.rejected_tokens.append(result)
        self.rejected_tokens = self.rejected_tokens[-20:]
        
        # Track rejection categories for performance metrics
        if not hasattr(self, 'rejection_stats'):
            self.rejection_stats = {}
        self.rejection_stats[category] = self.rejection_stats.get(category, 0) + 1
        
        # Add special logging for pump warnings
        if category in ['pump_warning', 'high_volume_ratio', 'excessive_volume', 'bad_distribution']:
            print(f"🚨 PUMP PROTECTION: {result['symbol']} - {'; '.join(reasons)}")
        else:
            print(f"❌ Token rejected ({category}): {result['symbol']} - {'; '.join(reasons)}")

    def get_analysis_status(self) -> Dict:
        """Get current analysis status"""
        status = {
            'is_running': self.is_running,
            'current_analysis': self.current_analysis,
            'approved_count': len(self.analysis_results),
            'rejected_count': len(self.rejected_tokens),
            'criteria': self.criteria
        }
        
        # Add performance metrics if available
        if hasattr(self, 'rejection_stats') and self.rejection_stats:
            status['rejection_stats'] = self.rejection_stats.copy()
            status['early_rejection_rate'] = self._calculate_early_rejection_rate()
        
        return status

    def _calculate_early_rejection_rate(self) -> Dict:
        """Calculate early rejection efficiency metrics"""
        if not hasattr(self, 'rejection_stats') or not self.rejection_stats:
            return {}
        
        total_rejections = sum(self.rejection_stats.values())
        early_categories = ['age_check', 'token_info', 'price_drop']
        early_rejections = sum(self.rejection_stats.get(cat, 0) for cat in early_categories)
        
        return {
            'total_rejections': total_rejections,
            'early_rejections': early_rejections,
            'early_rejection_percentage': round((early_rejections / total_rejections * 100) if total_rejections > 0 else 0, 1),
            'efficiency_saved': f"Saved {early_rejections} tokens from full analysis"
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

    def log_performance_metrics(self):
        """Log detailed performance metrics for optimization monitoring"""
        if not hasattr(self, 'rejection_stats') or not self.rejection_stats:
            print("📊 No performance metrics available yet")
            return
        
        print("=" * 60)
        print("📊 TOKEN ANALYZER PERFORMANCE METRICS")
        print("=" * 60)
        
        # Overall stats
        total_analyzed = sum(self.rejection_stats.values()) + len(self.analysis_results)
        total_rejected = sum(self.rejection_stats.values())
        total_approved = len(self.analysis_results)
        
        print(f"🔍 Total Tokens Analyzed: {total_analyzed}")
        print(f"✅ Approved: {total_approved} ({(total_approved/total_analyzed*100):.1f}%)")
        print(f"❌ Rejected: {total_rejected} ({(total_rejected/total_analyzed*100):.1f}%)")
        print()
        
        # Early rejection efficiency
        early_categories = ['age_check', 'token_info', 'price_drop']
        early_rejections = sum(self.rejection_stats.get(cat, 0) for cat in early_categories)
        late_categories = ['market_cap', 'liquidity', 'volume', 'holders', 'security_score', 'final_evaluation']
        late_rejections = sum(self.rejection_stats.get(cat, 0) for cat in late_categories)
        
        print("⚡ EARLY REJECTION EFFICIENCY:")
        print(f"   Early rejections: {early_rejections} ({(early_rejections/total_rejected*100):.1f}%)")
        print(f"   Late rejections: {late_rejections} ({(late_rejections/total_rejected*100):.1f}%)")
        print(f"   API calls saved: ~{early_rejections * 3} (estimated)")
        print()
        
        # Breakdown by rejection category
        print("📋 REJECTION BREAKDOWN:")
        for category in sorted(self.rejection_stats.keys(), key=lambda x: self.rejection_stats[x], reverse=True):
            count = self.rejection_stats[category]
            percentage = (count / total_rejected * 100) if total_rejected > 0 else 0
            emoji = "⚡" if category in early_categories else "🔍"
            print(f"   {emoji} {category:15}: {count:3d} ({percentage:5.1f}%)")
        
        print("=" * 60)