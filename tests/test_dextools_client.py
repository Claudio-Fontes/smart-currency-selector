#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from src.client import DEXToolsClient
from src.config import load_settings

load_dotenv()

def test_client():
    print("🧪 Teste do Cliente DEXTools")
    print("=" * 40)
    
    # Carregar configurações
    settings = load_settings()
    
    if not settings['dextools']['api_key']:
        print("❌ API key não configurada. Configure no .env antes de testar.")
        return
    
    # Inicializar cliente
    client = DEXToolsClient(
        settings['dextools']['api_key'],
        settings['dextools']['base_url']
    )
    
    # Token de teste na Solana
    test_chain = "solana"
    test_token = "egy3LC9ndbxo8LzL8W3s8FzwS3H6gT7t73uUP2Mpump"
    
    print(f"\n🔍 Testando com token na {test_chain.upper()}")
    print(f"   Endereço: {test_token}")
    
    try:
        # Teste 1: Buscar pools
        print("\n1️⃣ Testando busca de pools...")
        pool = client.get_token_pools(test_chain, test_token)
        if pool:
            print(f"   ✅ Pool encontrada: {pool['address'][:10]}...")
            print(f"   💰 Liquidez: ${pool.get('liquidity', {}).get('usd', 0):,.2f}")
        else:
            print("   ❌ Nenhuma pool encontrada")
        
        # Teste 2: Métricas de preço
        print("\n2️⃣ Testando métricas completas...")
        metrics = client.get_price_metrics(test_chain, test_token)
        print(f"   📌 Token: {metrics['token_name']} ({metrics['token_symbol']})")
        print(f"   💵 Preço: ${metrics['price_usd']:.8f}")
        print(f"   📊 Variação 24h: {metrics['price_change_24h']:.2f}%")
        print(f"   ⏱️  Variação 1h: {metrics['price_change_1h']:.2f}%")
        print(f"   📈 Market Cap: ${metrics['mcap']:,.2f}")
        print(f"   💧 Liquidez: ${metrics['liquidity_usd']:,.2f}")
        print(f"   📦 Volume 24h: ${metrics['volume_24h_usd']:,.2f}")
        print(f"   📦 Volume 1h: ${metrics['volume_1h_usd']:,.2f}")
        print(f"   📦 Volume 6h: ${metrics['volume_6h_usd']:,.2f}")
        print(f"   🪙 Supply: {metrics['circulating_supply']:,.0f} / {metrics['total_supply']:,.0f}")
        print(f"   👥 Holders: {metrics['holders_count']}")
        print(f"   🏪 DEX: {metrics['dex_info'].get('name', 'N/A')}")
        print(f"   🏊 Pool: {metrics['pool_address'][:10]}..." if metrics['pool_address'] else "   🏊 Pool: N/A")
        
        # Teste 3: Análise de holders
        print("\n3️⃣ Testando análise de holders...")
        holders = client.analyze_top_holders(test_chain, test_token, 5)
        if 'note' in holders:
            print(f"   👥 Total de holders: {holders['total_holders']}")
            print(f"   ℹ️  {holders['note']}")
        else:
            print(f"   👑 Top 5 holders detêm {holders['percentage']:.2f}% do supply")
        
        # Teste 4: Tendência de preço
        print("\n4️⃣ Testando tendência de preço...")
        trend = client.get_price_trend(test_chain, test_token)
        print(f"   📈 {trend}")
        
        # Teste 5: Verificação de segurança
        print("\n5️⃣ Testando verificação de segurança...")
        security = client.security_check(test_chain, test_token)
        for issue in security[:3]:  # Mostra apenas os 3 primeiros
            print(f"   {issue}")
        
        print("\n✅ Todos os testes executados com sucesso!")
        
    except Exception as e:
        print(f"\n❌ Erro durante o teste: {e}")

if __name__ == "__main__":
    test_client()