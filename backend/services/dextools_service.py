import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

class DEXToolsService:
    def __init__(self):
        self.api_key = os.getenv('DEXTOOLS_API_KEY')
        self.base_url = "https://public-api.dextools.io/standard/v2"
        self.headers = {"X-API-KEY": self.api_key}
        self._last_request_time = 0
        self.rate_limit_delay = 2.0

    def _make_request(self, url: str) -> requests.Response:
        """Make request with rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            time.sleep(sleep_time)
        
        response = requests.get(url, headers=self.headers)
        self._last_request_time = time.time()
        return response

    def get_hot_pools(self, limit: int = 50):
        """Get Solana hot pools - ALWAYS FRESH DATA
        If limit > 30, combines hot pools with gainers to reach 50 tokens
        """
        try:
            all_tokens = {}  # Use dict to avoid duplicates
            
            # Add timestamp to prevent any caching
            import datetime
            timestamp = datetime.datetime.now().isoformat()
            print(f"⏰ Fetching tokens at: {timestamp}")
            
            # First get hot pools (max 30)
            url = f"{self.base_url}/ranking/solana/hotpools"
            print(f"🔥 Fetching hot pools from: {url}")
            
            response = self._make_request(url)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict) and 'data' in data:
                    pools_list = data['data']
                    
                    # Add hot pools to collection
                    for pool in pools_list:
                        token = pool.get('mainToken', {})
                        address = token.get('address')
                        if address:
                            all_tokens[address] = pool
                    
                    print(f"✅ Got {len(pools_list)} hot pools")
                    
                    # If we need more than 30 tokens, get gainers too
                    if limit > 30 and len(all_tokens) < limit:
                        url_gainers = f"{self.base_url}/ranking/solana/gainers"
                        print(f"📈 Fetching gainers to reach {limit} tokens...")
                        
                        response_gainers = self._make_request(url_gainers)
                        
                        if response_gainers.status_code == 200:
                            data_gainers = response_gainers.json()
                            if isinstance(data_gainers, dict) and 'data' in data_gainers:
                                gainers_list = data_gainers.get('data', [])
                                
                                # Add gainers to collection (avoiding duplicates)
                                added_gainers = 0
                                for pool in gainers_list:
                                    token = pool.get('mainToken', {})
                                    address = token.get('address')
                                    if address and address not in all_tokens:
                                        all_tokens[address] = pool
                                        added_gainers += 1
                                        if len(all_tokens) >= limit:
                                            break
                                
                                print(f"✅ Added {added_gainers} gainers (total: {len(all_tokens)} tokens)")
                    
                    # Convert to list and return requested limit
                    final_list = list(all_tokens.values())[:limit]
                    
                    # Log first few pools for debugging
                    if final_list:
                        print(f"📊 Returning {len(final_list)} tokens")
                        for i in range(min(3, len(final_list))):
                            token = final_list[i].get('mainToken', {})
                            print(f"   #{i+1} {token.get('symbol', '?')} - {token.get('name', 'Unknown')[:20]}")
                    
                    return final_list
            else:
                print(f"❌ API returned status: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
            return []
        except Exception as e:
            print(f"❌ Error fetching hot pools: {e}")
            return []
    
    def get_hot_pools_with_social(self, limit: int = 50):
        """Get Solana hot pools with enhanced social metrics"""
        try:
            pools = self.get_hot_pools(limit)
            
            # Enriquecer cada pool com métricas sociais
            for pool in pools:
                main_token = pool.get('mainToken', {})
                token_address = main_token.get('address')
                
                if token_address:
                    # Buscar informações do token
                    token_info = self.get_token_info(token_address)
                    
                    if token_info and token_info.get('success'):
                        social_info = token_info.get('data', {}).get('socialInfo', {})
                        
                        # Calcular métricas sociais
                        social_count = sum(1 for v in social_info.values() if v and v != 'N/A' and v != '')
                        
                        social_score = 0
                        if social_info.get('website'):
                            social_score += 30
                        if social_info.get('twitter'):
                            social_score += 25
                        if social_info.get('telegram'):
                            social_score += 25
                        if social_info.get('discord'):
                            social_score += 10
                        if social_info.get('github'):
                            social_score += 10
                        
                        pool['socialMetrics'] = {
                            'score': social_score,
                            'count': social_count,
                            'hasTwitter': bool(social_info.get('twitter')),
                            'hasTelegram': bool(social_info.get('telegram')),
                            'hasWebsite': bool(social_info.get('website'))
                        }
                        
                        pool['socialInfo'] = social_info
                        
                        # Classificar momentum social
                        if social_score >= 80:
                            pool['socialMomentum'] = 'STRONG 🔥'
                        elif social_score >= 60:
                            pool['socialMomentum'] = 'MODERATE 📈'
                        elif social_score >= 40:
                            pool['socialMomentum'] = 'GROWING 🌱'
                        else:
                            pool['socialMomentum'] = 'LOW 💤'
                    else:
                        # Se não conseguir info social
                        pool['socialMetrics'] = {
                            'score': 0,
                            'count': 0,
                            'hasTwitter': False,
                            'hasTelegram': False,
                            'hasWebsite': False
                        }
                        pool['socialMomentum'] = 'UNKNOWN ❓'
            
            return pools
        except Exception as e:
            print(f"Error fetching hot pools with social: {e}")
            return []

    def get_token_info(self, token_address: str):
        """Get detailed token information"""
        try:
            url = f"{self.base_url}/token/solana/{token_address}"
            response = self._make_request(url)
            
            if response.status_code == 200:
                json_response = response.json()
                # DexTools already returns {statusCode, data} format
                if json_response.get('statusCode') == 200:
                    return {
                        'success': True,
                        'statusCode': 200,
                        'data': json_response.get('data', {})
                    }
                else:
                    return {
                        'success': False,
                        'statusCode': json_response.get('statusCode', 500),
                        'error': 'API returned error status'
                    }
            else:
                return {
                    'success': False,
                    'statusCode': response.status_code,
                    'error': f"HTTP {response.status_code}"
                }
        except Exception as e:
            print(f"Error fetching token info: {e}")
            return {
                'success': False,
                'statusCode': 500,
                'error': str(e)
            }

    def get_token_price(self, token_address: str):
        """Get token price information"""
        try:
            url = f"{self.base_url}/token/solana/{token_address}/price"
            response = self._make_request(url)
            
            if response.status_code == 200:
                json_response = response.json()
                # DexTools already returns {statusCode, data} format
                if json_response.get('statusCode') == 200:
                    return {
                        'success': True,
                        'statusCode': 200,
                        'data': json_response.get('data', {})
                    }
                else:
                    return {
                        'success': False,
                        'statusCode': json_response.get('statusCode', 500),
                        'error': 'API returned error status'
                    }
            else:
                return {
                    'success': False,
                    'statusCode': response.status_code,
                    'error': f"HTTP {response.status_code}"
                }
        except Exception as e:
            print(f"Error fetching token price: {e}")
            return {
                'success': False,
                'statusCode': 500,
                'error': str(e)
            }

    def get_token_price_history(self, token_address: str):
        """Get token price history with more granular data"""
        try:
            url = f"{self.base_url}/token/solana/{token_address}/price/history"
            response = self._make_request(url)
            
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Error fetching token price history: {e}")
            return None

    def get_token_score(self, token_address: str):
        """Get token security score"""
        try:
            url = f"{self.base_url}/token/solana/{token_address}/score"
            response = self._make_request(url)
            
            if response.status_code == 200:
                json_response = response.json()
                # DexTools already returns {statusCode, data} format
                if json_response.get('statusCode') == 200:
                    return {
                        'success': True,
                        'statusCode': 200,
                        'data': json_response.get('data', {})
                    }
                else:
                    return {
                        'success': False,
                        'statusCode': json_response.get('statusCode', 500),
                        'error': 'API returned error status'
                    }
            else:
                return {
                    'success': False,
                    'statusCode': response.status_code,
                    'error': f"HTTP {response.status_code}"
                }
        except Exception as e:
            print(f"Error fetching token score: {e}")
            return {
                'success': False,
                'statusCode': 500,
                'error': str(e)
            }

    def get_complete_token_analysis(self, token_address: str):
        """Get complete token analysis combining multiple endpoints"""
        print(f"💧 Complete analysis started for: {token_address}")
        analysis = {
            'token_address': token_address,
            'info': None,
            'price': None,
            'score': None,
            'metrics': None,
            'audit': None,
            'tax_analysis': None,
            'success': False
        }
        
        # Get token info
        analysis['info'] = self.get_token_info(token_address)
        
        # Get token price
        analysis['price'] = self.get_token_price(token_address)
        
        # Get token score
        analysis['score'] = self.get_token_score(token_address)
        
        # Get comprehensive metrics (liquidez, volume, etc)
        analysis['metrics'] = self.get_token_metrics(token_address)
        
        # Get audit and tax information
        analysis['audit'] = self.get_token_audit(token_address)
        analysis['tax_analysis'] = self.get_token_tax_analysis(token_address)
        
        analysis['success'] = any([analysis['info'], analysis['price'], analysis['score'], analysis['metrics']])
        
        return analysis

    def get_token_metrics(self, token_address: str):
        """Get comprehensive token metrics using multiple DexTools endpoints like the original client"""
        print(f"💧 Starting get_token_metrics for {token_address}")
        try:
            base_data = {}
            
            # Use the same approach as the original DexTools client
            # First get token pools to find the main pool
            pools = self._get_token_pools_for_metrics(token_address)
            main_pool = None
            
            if pools and isinstance(pools, list) and len(pools) > 0:
                # NEW LOGIC: Find the best pool based on ACTUAL LIQUIDITY
                best_pool = None
                best_liquidity = 0
                dex_priority = {'Raydium': 3, 'Orca': 2, 'Meteora': 1}  # Priority scores
                
                print(f"💧 Testing liquidity for {len(pools)} pools...")
                
                for pool in pools:
                    if isinstance(pool, dict):
                        pool_address = pool.get('address', '')
                        exchange = pool.get('exchange', {})
                        exchange_name = exchange.get('name', '') if isinstance(exchange, dict) else ''
                        
                        # Skip Pump.fun pools (they rarely have real liquidity)
                        if 'Pump.fun' in exchange_name:
                            print(f"💧 Skipping Pump.fun pool: {pool_address}")
                            continue
                        
                        # Test actual liquidity
                        try:
                            liquidity_url = f"{self.base_url}/pool/solana/{pool_address}/liquidity"
                            response = self._make_request(liquidity_url)
                            
                            if response.status_code == 200:
                                json_response = response.json()
                                if json_response.get('statusCode') == 200:
                                    liquidity_data = json_response.get('data', {})
                                    liquidity_value = liquidity_data.get('liquidity', 0)
                                    
                                    # Also check reserves if liquidity is None
                                    if not liquidity_value and 'reserves' in liquidity_data:
                                        reserves = liquidity_data['reserves']
                                        if isinstance(reserves, dict):
                                            total_reserves = sum(v for v in reserves.values() if isinstance(v, (int, float)))
                                            liquidity_value = total_reserves
                                    
                                    print(f"💧 Pool {exchange_name} ({pool_address}): liquidity=${liquidity_value}")
                                    
                                    # Select best pool based on liquidity + DEX priority
                                    if liquidity_value and liquidity_value > 0:
                                        priority_bonus = dex_priority.get(exchange_name.split()[0], 0) * 100  # Small bonus for preferred DEXs
                                        total_score = liquidity_value + priority_bonus
                                        
                                        if total_score > best_liquidity:
                                            best_pool = pool
                                            best_liquidity = total_score
                                            print(f"💧 New best pool: {exchange_name} with ${liquidity_value} liquidity")
                            
                            # Rate limiting
                            time.sleep(0.5)
                        except Exception as e:
                            print(f"💧 Error testing liquidity for {pool_address}: {e}")
                
                # Fallback to first pool if no liquidity found
                if not best_pool:
                    print(f"💧 No pools with liquidity found, using first available")
                    best_pool = pools[0]
                
                main_pool = best_pool
                pool_address = main_pool.get('address', 'NO_ADDRESS')
                exchange_info = main_pool.get('exchange', {})
                exchange_name = exchange_info.get('name', 'UNKNOWN') if isinstance(exchange_info, dict) else 'UNKNOWN'
                
                print(f"💧 Found {len(pools)} pools, selected: {exchange_name}")
                print(f"💧 Selected pool address: {pool_address}")
            
            if main_pool and main_pool.get('address'):
                pool_address = main_pool['address']
                
                # Get pool liquidity using the correct endpoint
                pool_liquidity_data = self._get_pool_detailed_info(pool_address)
                if pool_liquidity_data:
                    base_data.update(pool_liquidity_data)
            
            # Get token info data
            token_info = self._get_token_detailed_info(token_address)
            if token_info:
                base_data.update(token_info)
            
            # Get price data
            price_info = self._get_token_price_info(token_address) 
            if price_info:
                base_data.update(price_info)
            
            # Final metrics with defaults
            final_metrics = {
                'liquidity_usd': base_data.get('liquidity_usd', 0),
                'volume_24h_usd': base_data.get('volume_24h_usd', 0), 
                'volume_1h_usd': base_data.get('volume_1h_usd', 0),
                'volume_6h_usd': base_data.get('volume_6h_usd', 0),
                'mcap': base_data.get('mcap', 0),
                'fdv': base_data.get('fdv', 0),
                'circulating_supply': base_data.get('circulating_supply', 0),
                'total_supply': base_data.get('total_supply', 0),
                'holders_count': base_data.get('holders_count', 0),
                'transactions': base_data.get('transactions', 0),
                'pool_address': main_pool.get('address', '') if main_pool else '',
                'dex_info': main_pool.get('exchange', {}) if main_pool else {}
            }
            
            print(f"💧 Final metrics: liquidity={final_metrics['liquidity_usd']}, volume24h={final_metrics['volume_24h_usd']}")
            
            return {
                'success': True,
                'statusCode': 200,
                'data': final_metrics
            }
            
        except Exception as e:
            print(f"Error in get_token_metrics: {e}")
            return {
                'success': False,
                'statusCode': 500,
                'error': str(e)
            }

    def _get_token_pools(self, token_address: str):
        """Get token pools information"""
        try:
            url = f"{self.base_url}/token/solana/{token_address}/pools"
            response = self._make_request(url)
            
            if response.status_code == 200:
                json_response = response.json()
                if json_response.get('statusCode') == 200:
                    return json_response.get('data')
            return None
        except Exception as e:
            print(f"Error fetching token pools: {e}")
            return None

    def _get_token_pools_for_metrics(self, token_address: str):
        """Get token pools specifically for metrics (copy of original client logic)"""
        try:
            url = f"{self.base_url}/token/solana/{token_address}/pools?sort=creationTime&order=desc&from=2020-01-01T00:00:00.000Z&to=2026-01-01T00:00:00.000Z"
            print(f"💧 Pools endpoint: {url}")
            response = self._make_request(url)
            
            if response.status_code == 200:
                json_response = response.json()
                print(f"💧 Pools response statusCode: {json_response.get('statusCode')}")
                if json_response.get('statusCode') == 200:
                    data = json_response.get('data', {})
                    print(f"💧 Pools data keys: {list(data.keys())}")
                    pools = data.get('results', [])
                    print(f"💧 Found {len(pools)} pools for metrics")
                    return pools
                else:
                    print(f"💧 Pools API error: {json_response}")
            else:
                print(f"💧 Pools for metrics failed: HTTP {response.status_code}")
                print(f"💧 Pools error response: {response.text[:200]}")
            return None
        except Exception as e:
            print(f"Error fetching pools for metrics: {e}")
            return None
    
    def _get_pool_detailed_info(self, pool_address: str):
        """Get detailed pool info including liquidity and volume (from original client)"""
        try:
            result = {}
            
            # Try pool liquidity endpoint
            liquidity_url = f"{self.base_url}/pool/solana/{pool_address}/liquidity"
            print(f"💧 Calling pool liquidity: {liquidity_url}")
            response = self._make_request(liquidity_url)
            
            if response.status_code == 200:
                json_response = response.json()
                if json_response.get('statusCode') == 200:
                    liquidity_data = json_response.get('data', {})
                    print(f"💧 Pool liquidity response keys: {list(liquidity_data.keys())}")
                    liquidity_value = liquidity_data.get('liquidity', 0)
                    print(f"💧 Pool liquidity raw value: {liquidity_value}")
                    
                    # Try to extract from reserves if liquidity is None/0
                    if not liquidity_value and 'reserves' in liquidity_data:
                        reserves = liquidity_data['reserves']
                        print(f"💧 Reserves data: {reserves}")
                        if isinstance(reserves, dict):
                            # Try to sum reserves or get total
                            total_reserves = 0
                            for key, value in reserves.items():
                                if isinstance(value, (int, float)):
                                    total_reserves += value
                            if total_reserves > 0:
                                liquidity_value = total_reserves
                                print(f"💧 Using reserves as liquidity: {liquidity_value}")
                    
                    result['liquidity_usd'] = liquidity_value if liquidity_value else 0
                else:
                    print(f"💧 Pool liquidity API error: {json_response.get('statusCode')}")
            else:
                print(f"💧 Pool liquidity HTTP error: {response.status_code}")
                
            # Try pool price endpoint for volume
            price_url = f"{self.base_url}/pool/solana/{pool_address}/price"
            print(f"💧 Calling pool price: {price_url}")
            response = self._make_request(price_url)
            
            if response.status_code == 200:
                json_response = response.json()
                if json_response.get('statusCode') == 200:
                    price_data = json_response.get('data', {})
                    print(f"💧 Pool price response keys: {list(price_data.keys())}")
                    volume24h = price_data.get('volume24h', 0)
                    volume1h = price_data.get('volume1h', 0)
                    volume6h = price_data.get('volume6h', 0)
                    print(f"💧 Pool volumes: 24h={volume24h}, 1h={volume1h}, 6h={volume6h}")
                    # Check for backup liquidity source
                    backup_liquidity = price_data.get('liquidity', 0)
                    print(f"💧 Pool price liquidity backup: {backup_liquidity}")
                    
                    result.update({
                        'volume_24h_usd': volume24h,
                        'volume_1h_usd': volume1h, 
                        'volume_6h_usd': volume6h,
                        # Use backup liquidity if primary is 0/None
                        'liquidity_usd': result.get('liquidity_usd', 0) or backup_liquidity
                    })
                else:
                    print(f"💧 Pool price API error: {json_response.get('statusCode')}")
            else:
                print(f"💧 Pool price HTTP error: {response.status_code}")
                
            return result
        except Exception as e:
            print(f"Error in _get_pool_detailed_info: {e}")
            return {}
    
    def _get_token_detailed_info(self, token_address: str):
        """Get detailed token info (from original client pattern)"""
        try:
            url = f"{self.base_url}/token/solana/{token_address}/info"
            response = self._make_request(url)
            
            if response.status_code == 200:
                json_response = response.json()
                if json_response.get('statusCode') == 200:
                    info_data = json_response.get('data', {})
                    return {
                        'mcap': info_data.get('mcap', 0),
                        'fdv': info_data.get('fdv', 0),
                        'circulating_supply': info_data.get('circulatingSupply', 0),
                        'total_supply': info_data.get('totalSupply', 0),
                        'holders_count': int(info_data.get('holders', 0)) if str(info_data.get('holders', 0)).isdigit() else 0,
                        'transactions': info_data.get('transactions', 0)
                    }
            return {}
        except Exception as e:
            print(f"Error in _get_token_detailed_info: {e}")
            return {}
    
    def _get_token_price_info(self, token_address: str):
        """Get token price info (from original client pattern)"""
        try:
            url = f"{self.base_url}/token/solana/{token_address}/price"
            response = self._make_request(url)
            
            if response.status_code == 200:
                json_response = response.json()
                if json_response.get('statusCode') == 200:
                    price_data = json_response.get('data', {})
                    print(f"💧 Token price response keys: {list(price_data.keys())}")
                    # Some price endpoints may have volume/liquidity data
                    result = {}
                    if 'volume24h' in price_data:
                        result['volume_24h_usd'] = price_data.get('volume24h', 0)
                    if 'liquidity' in price_data:
                        result['liquidity_usd'] = price_data.get('liquidity', 0) 
                    return result
            return {}
        except Exception as e:
            print(f"Error in _get_token_price_info: {e}")
            return {}

    def _get_pool_liquidity(self, pool_address: str):
        """Get pool liquidity information using correct endpoints"""
        try:
            # Use specific liquidity endpoint
            liquidity_url = f"{self.base_url}/pool/solana/{pool_address}/liquidity"
            price_url = f"{self.base_url}/pool/solana/{pool_address}/price"
            
            print(f"💧 Trying pool liquidity endpoint: {liquidity_url}")
            liquidity_response = self._make_request(liquidity_url)
            liquidity_data = {}
            
            if liquidity_response.status_code == 200:
                json_response = liquidity_response.json()
                if json_response.get('statusCode') == 200:
                    liquidity_data = json_response.get('data', {})
                    print(f"💧 Pool liquidity data keys: {list(liquidity_data.keys())}")
                    print(f"💧 Pool liquidity value: {liquidity_data.get('liquidity', 'NOT_FOUND')}")
                else:
                    print(f"💧 Pool liquidity endpoint failed: {json_response.get('statusCode')}")
            else:
                print(f"💧 Pool liquidity HTTP error: {liquidity_response.status_code}")
            
            # Get volume data from price endpoint
            print(f"💧 Trying pool price endpoint: {price_url}")
            price_response = self._make_request(price_url)
            volume_data = {}
            
            if price_response.status_code == 200:
                json_response = price_response.json()
                if json_response.get('statusCode') == 200:
                    volume_data = json_response.get('data', {})
                    print(f"💧 Pool price data keys: {list(volume_data.keys())}")
                    print(f"💧 Pool volume24h: {volume_data.get('volume24h', 'NOT_FOUND')}")
                    print(f"💧 Pool liquidity from price: {volume_data.get('liquidity', 'NOT_FOUND')}")
                else:
                    print(f"💧 Pool price endpoint failed: {json_response.get('statusCode')}")
            else:
                print(f"💧 Pool price HTTP error: {price_response.status_code}")
            
            result = {
                'liquidity_usd': liquidity_data.get('liquidity', volume_data.get('liquidity', 0)),
                'volume_24h_usd': volume_data.get('volume24h', 0),
                'volume_1h_usd': volume_data.get('volume1h', 0),
                'volume_6h_usd': volume_data.get('volume6h', 0),
                'pool_address': pool_address,
                'dex_info': volume_data.get('exchange', {})
            }
            
            print(f"💧 Final pool result: liquidity={result['liquidity_usd']}, volume24h={result['volume_24h_usd']}")
            return result
            
        except Exception as e:
            print(f"Error fetching pool liquidity: {e}")
            return {}

    def get_token_audit(self, token_address: str):
        """Get token audit information including taxes"""
        try:
            # Import the complete client
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
            from client.dextools_client import DEXToolsClient
            
            # Initialize the complete client
            client = DEXToolsClient(
                api_key=self.api_key,
                base_url=self.base_url,
                rate_limit_delay=self.rate_limit_delay
            )
            
            # Get audit data
            audit_data = client.get_token_audit("solana", token_address)
            
            return {
                'statusCode': 200,
                'data': audit_data
            }
            
        except Exception as e:
            print(f"Error fetching token audit: {e}")
            return None

    def get_token_tax_analysis(self, token_address: str):
        """Get detailed tax analysis for token"""
        try:
            # Import the complete client
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
            from client.dextools_client import DEXToolsClient
            
            # Initialize the complete client
            client = DEXToolsClient(
                api_key=self.api_key,
                base_url=self.base_url,
                rate_limit_delay=self.rate_limit_delay
            )
            
            # Get tax analysis
            tax_analysis = client.analyze_token_taxes("solana", token_address)
            
            return {
                'statusCode': 200,
                'data': tax_analysis
            }
            
        except Exception as e:
            print(f"Error fetching token tax analysis: {e}")
            return None