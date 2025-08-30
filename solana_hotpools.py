#!/usr/bin/env python3

import sys
import os
import time
import argparse
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
import requests

load_dotenv()

class SolanaHotPoolsClient:
    def __init__(self, api_key, base_url="https://public-api.dextools.io/standard/v2"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {"X-API-KEY": api_key}
        self._last_request_time = 0
        self.rate_limit_delay = 2.0

    def _make_request(self, url: str) -> requests.Response:
        """Faz request com rate limiting para evitar 429"""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            print(f"⏱️  Aguardando {sleep_time:.1f}s para evitar rate limit...")
            time.sleep(sleep_time)
        
        response = requests.get(url, headers=self.headers)
        self._last_request_time = time.time()
        return response

    def get_hot_pools(self, limit: int = 30):
        """
        Busca as hot pools da Solana
        
        Args:
            limit: Número de pools para retornar (padrão: 30)
        
        Returns:
            Lista das hot pools com dados completos
        """
        try:
            url = f"{self.base_url}/ranking/solana/hotpools"
            print(f"🔥 Buscando top {limit} hot pools da SOLANA...")
            
            response = self._make_request(url)
            
            if response.status_code == 200:
                data = response.json()
                
                # API retorna {statusCode: 200, data: [...]}
                if isinstance(data, dict) and 'data' in data:
                    pools_list = data['data']
                else:
                    print(f"❌ Formato inesperado da API: {type(data)}")
                    return []
                
                # Limitar ao número solicitado
                hot_pools = pools_list[:limit] if len(pools_list) > limit else pools_list
                
                return hot_pools
            else:
                print(f"❌ Erro na API: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            print(f"❌ Erro ao buscar hot pools: {e}")
            return []

    def display_hot_pools(self, hot_pools: list):
        """Exibe as hot pools de forma formatada"""
        if not hot_pools:
            print("❌ Nenhuma hot pool encontrada")
            return
        
        print(f"\n🔥 TOP {len(hot_pools)} HOT POOLS - SOLANA")
        print("=" * 60)
        
        for i, pool in enumerate(hot_pools, 1):
            main_token = pool.get('mainToken', {})
            side_token = pool.get('sideToken', {})
            exchange_info = pool.get('exchange', {})
            
            # Formatação do endereço da pool
            pool_address = pool.get('address', 'N/A')
            pool_short = f"{pool_address[:8]}...{pool_address[-6:]}" if len(pool_address) > 14 else pool_address
            
            # Símbolos dos tokens
            main_symbol = main_token.get('symbol', 'N/A')
            side_symbol = side_token.get('symbol', 'N/A')
            
            print(f"\n#{i:2d} 🏆 {main_symbol}/{side_symbol}")
            print(f"     🏊 {pool_short}")
            print(f"     🏪 {exchange_info.get('name', 'N/A')}")
            print(f"     🪙 {main_token.get('name', 'N/A')}")
            
            # Data de criação formatada
            if 'creationTime' in pool:
                creation_date = pool['creationTime'][:10] if len(pool['creationTime']) > 10 else pool['creationTime']
                print(f"     📅 {creation_date}")

    def save_to_file(self, hot_pools: list, limit: int):
        """Salva os resultados em arquivo"""
        filename = f"solana_hotpools_top{limit}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"🔥 TOP {len(hot_pools)} HOT POOLS - SOLANA\n")
            f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 60 + "\n\n")
            
            for i, pool in enumerate(hot_pools, 1):
                main_token = pool.get('mainToken', {})
                side_token = pool.get('sideToken', {})
                exchange_info = pool.get('exchange', {})
                
                f.write(f"#{i:2d} - {main_token.get('symbol', 'N/A')}/{side_token.get('symbol', 'N/A')}\n")
                f.write(f"Pool Address: {pool.get('address', 'N/A')}\n")
                f.write(f"DEX: {exchange_info.get('name', 'N/A')}\n")
                f.write(f"Main Token: {main_token.get('name', 'N/A')} ({main_token.get('symbol', 'N/A')})\n")
                f.write(f"Side Token: {side_token.get('name', 'N/A')} ({side_token.get('symbol', 'N/A')})\n")
                f.write(f"Rank: {pool.get('rank', 'N/A')}\n")
                
                if 'creationTime' in pool:
                    f.write(f"Created: {pool['creationTime'][:19]}\n")
                
                f.write("-" * 50 + "\n\n")
        
        print(f"✅ Arquivo salvo: {filename}")
        return filename

def main():
    parser = argparse.ArgumentParser(description="🔥 Solana Hot Pools - DEXTools API Client")
    parser.add_argument("limit", nargs="?", type=int, default=30, help="Número de pools (padrão: 30)")
    parser.add_argument("-s", "--save", action="store_true", help="Salvar em arquivo")
    
    args = parser.parse_args()
    
    print("🔥 SOLANA HOT POOLS - DEXTools")
    print("=" * 35)
    
    # Carregar API key
    api_key = os.getenv('DEXTOOLS_API_KEY')
    if not api_key:
        print("❌ DEXTOOLS_API_KEY não encontrada no .env")
        print("💡 Configure sua API key no arquivo .env")
        return
    
    # Validar limite
    limit = min(max(args.limit, 1), 100)  # Entre 1 e 100
    if limit != args.limit:
        print(f"⚠️  Limite ajustado para {limit} (máx: 100)")
    
    # Inicializar cliente
    client = SolanaHotPoolsClient(api_key)
    
    # Buscar hot pools
    hot_pools = client.get_hot_pools(limit)
    
    # Exibir resultados
    if hot_pools:
        client.display_hot_pools(hot_pools)
        print(f"\n✅ {len(hot_pools)} hot pools encontradas")
        
        # Salvar se solicitado
        if args.save:
            client.save_to_file(hot_pools, limit)
    else:
        print("❌ Nenhuma hot pool encontrada")

if __name__ == "__main__":
    main()