#!/usr/bin/env python3

import sys
import os
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
import requests

load_dotenv()

class HotPoolsClient:
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

    def get_hot_pools(self, chain: str, limit: int = 30):
        """
        Busca as hot pools (pools mais quentes/populares) de uma blockchain
        
        Args:
            chain: Nome da blockchain (ex: 'solana', 'ether', 'bsc')
            limit: Número de pools para retornar (padrão: 30)
        
        Returns:
            Lista das hot pools com dados completos
        """
        try:
            url = f"{self.base_url}/ranking/{chain}/hotpools"
            print(f"🔥 Buscando hot pools na {chain.upper()}...")
            
            response = self._make_request(url)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verificar se tem estrutura de sucesso da API
                if isinstance(data, dict) and 'data' in data:
                    # API retorna {statusCode: 200, data: [...]}
                    pools_list = data['data']
                elif isinstance(data, list):
                    # API retorna diretamente [...]
                    pools_list = data
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

    def display_hot_pools(self, hot_pools: list, chain: str):
        """
        Exibe as hot pools de forma formatada
        
        Args:
            hot_pools: Lista de hot pools da API
            chain: Nome da blockchain
        """
        if not hot_pools:
            print("❌ Nenhuma hot pool encontrada")
            return
        
        print(f"\n🔥 TOP {len(hot_pools)} HOT POOLS - {chain.upper()}")
        print("=" * 80)
        
        for i, pool in enumerate(hot_pools, 1):
            main_token = pool.get('mainToken', {})
            side_token = pool.get('sideToken', {})
            exchange_info = pool.get('exchange', {})
            
            # Formatação do endereço da pool
            pool_address = pool.get('address', 'N/A')
            pool_short = f"{pool_address[:10]}...{pool_address[-6:]}" if len(pool_address) > 16 else pool_address
            
            print(f"\n#{i:2d} - {main_token.get('symbol', 'N/A')}/{side_token.get('symbol', 'N/A')}")
            print(f"     🏊 Pool: {pool_short}")
            print(f"     🏪 DEX: {exchange_info.get('name', 'N/A')}")
            print(f"     📈 Rank: {pool.get('rank', 'N/A')}")
            print(f"     🪙 Main Token: {main_token.get('name', 'N/A')} ({main_token.get('symbol', 'N/A')})")
            print(f"     💰 Side Token: {side_token.get('name', 'N/A')} ({side_token.get('symbol', 'N/A')})")
            print(f"     💳 Fee: {pool.get('fee', 0)}%")
            
            # Dados de criação se disponíveis
            if 'creationTime' in pool:
                creation_time = pool['creationTime'][:19] if len(pool['creationTime']) > 19 else pool['creationTime']
                print(f"     📅 Criado em: {creation_time}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Cliente de Hot Pools - DEXTools")
    parser.add_argument("-c", "--chain", default="solana", help="Blockchain (sempre solana por padrão)")
    parser.add_argument("-l", "--limit", type=int, default=30, help="Número de pools (padrão: 30)")
    parser.add_argument("-s", "--save", action="store_true", help="Salvar resultados em arquivo")
    
    args = parser.parse_args()
    
    print("🔥 Hot Pools Solana - DEXTools")
    print("=" * 40)
    
    # Carregar configurações
    api_key = os.getenv('DEXTOOLS_API_KEY')
    if not api_key:
        print("❌ DEXTOOLS_API_KEY não encontrada no .env")
        return
    
    # Inicializar cliente
    client = HotPoolsClient(api_key)
    
    chain = args.chain.lower()
    limit = min(args.limit, 100)  # Máximo 100 pools
    
    if limit != args.limit:
        print("⚠️  Limitando a 100 pools máximo")
    
    # Buscar hot pools
    hot_pools = client.get_hot_pools(chain, limit)
    
    # Exibir resultados
    if hot_pools:
        client.display_hot_pools(hot_pools, chain)
        print(f"\n✅ {len(hot_pools)} hot pools encontradas em {chain.upper()}")
        
        # Salvar em arquivo
        if args.save:
            filename = f"hot_pools_{chain}_{len(hot_pools)}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"HOT POOLS - {chain.upper()} - {len(hot_pools)} pools\n")
                f.write("=" * 60 + "\n\n")
                
                for i, pool in enumerate(hot_pools, 1):
                    main_token = pool.get('mainToken', {})
                    side_token = pool.get('sideToken', {})
                    exchange_info = pool.get('exchange', {})
                    
                    f.write(f"#{i:2d} - {main_token.get('symbol', 'N/A')}/{side_token.get('symbol', 'N/A')}\n")
                    f.write(f"Pool: {pool.get('address', 'N/A')}\n")
                    f.write(f"DEX: {exchange_info.get('name', 'N/A')}\n")
                    f.write(f"Rank: {pool.get('rank', 'N/A')}\n")
                    f.write(f"Main Token: {main_token.get('name', 'N/A')} ({main_token.get('symbol', 'N/A')})\n")
                    f.write(f"Side Token: {side_token.get('name', 'N/A')} ({side_token.get('symbol', 'N/A')})\n")
                    f.write(f"Fee: {pool.get('fee', 0)}%\n")
                    
                    if 'creationTime' in pool:
                        creation_time = pool['creationTime'][:19] if len(pool['creationTime']) > 19 else pool['creationTime']
                        f.write(f"Criado em: {creation_time}\n")
                    
                    f.write("-" * 40 + "\n\n")
            
            print(f"✅ Arquivo salvo: {filename}")
    
    else:
        print(f"❌ Nenhuma hot pool encontrada para {chain}")

if __name__ == "__main__":
    main()