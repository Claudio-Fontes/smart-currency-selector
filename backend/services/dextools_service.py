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

    def get_hot_pools(self, limit: int = 30):
        """Get Solana hot pools"""
        try:
            url = f"{self.base_url}/ranking/solana/hotpools"
            response = self._make_request(url)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict) and 'data' in data:
                    pools_list = data['data']
                    return pools_list[:limit] if len(pools_list) > limit else pools_list
            return []
        except Exception as e:
            print(f"Error fetching hot pools: {e}")
            return []

    def get_token_info(self, token_address: str):
        """Get detailed token information"""
        try:
            url = f"{self.base_url}/token/solana/{token_address}"
            response = self._make_request(url)
            
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Error fetching token info: {e}")
            return None

    def get_token_price(self, token_address: str):
        """Get token price information"""
        try:
            url = f"{self.base_url}/token/solana/{token_address}/price"
            response = self._make_request(url)
            
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Error fetching token price: {e}")
            return None

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
                return response.json()
            return None
        except Exception as e:
            print(f"Error fetching token score: {e}")
            return None

    def get_complete_token_analysis(self, token_address: str):
        """Get complete token analysis combining multiple endpoints"""
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
        """Get comprehensive token metrics including liquidity, volume, etc"""
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
            
            # Get comprehensive metrics
            metrics = client.get_price_metrics("solana", token_address)
            
            return {
                'statusCode': 200,
                'data': metrics
            }
            
        except Exception as e:
            print(f"Error fetching token metrics: {e}")
            return None

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