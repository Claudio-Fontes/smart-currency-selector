#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from src.client import DEXToolsClient
from src.config import load_settings
import requests

load_dotenv()

def test_holders_endpoints():
    print("🧪 Teste Específico de Holders")
    print("=" * 40)
    
    settings = load_settings()
    
    if not settings['dextools']['api_key']:
        print("❌ API key não configurada")
        return
    
    api_key = settings['dextools']['api_key']
    base_url = settings['dextools']['base_url'].rstrip('/')
    headers = {
        "accept": "application/json",
        "X-API-Key": api_key
    }
    
    # Token de teste - vamos usar um token popular
    test_chain = "ether"  # Ethereum tem mais dados
    test_token = "0xfb7b4564402e5500db5bb6d63ae671302777c75a"  # DEXT token
    
    print(f"\n🔍 Testando com DEXT token no Ethereum")
    print(f"   Endereço: {test_token}")
    
    # Teste 1: Endpoint direto /holders (se existir)
    print("\n1️⃣ Testando endpoint direto /holders...")
    holders_url = f"{base_url}/token/{test_chain}/{test_token}/holders"
    
    try:
        response = requests.get(holders_url, headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Dados obtidos: {len(data.get('data', []))} holders")
            if data.get('data'):
                for i, holder in enumerate(data['data'][:5], 1):
                    print(f"   {i}. {holder.get('address', 'N/A')[:10]}... - {holder.get('balance', 0)}")
        else:
            print(f"   ❌ Erro: {response.text}")
    except Exception as e:
        print(f"   ❌ Erro na requisição: {e}")
    
    # Teste 2: Variações do endpoint
    print("\n2️⃣ Testando variações do endpoint...")
    
    endpoints_to_test = [
        f"/token/{test_chain}/{test_token}/holders?limit=10",
        f"/token/{test_chain}/{test_token}/holders?page=0&pageSize=10", 
        f"/token/{test_chain}/{test_token}/top-holders",
        f"/token/{test_chain}/{test_token}/distribution"
    ]
    
    for endpoint in endpoints_to_test:
        url = base_url + endpoint
        try:
            response = requests.get(url, headers=headers)
            print(f"   {endpoint}: Status {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"     ✅ Dados encontrados!")
                if 'data' in data and isinstance(data['data'], list):
                    print(f"     📊 {len(data['data'])} itens retornados")
        except Exception as e:
            print(f"     ❌ Erro: {e}")
    
    # Teste 3: Usando cliente atual (com método corrigido)
    print("\n3️⃣ Testando com cliente corrigido...")
    client = DEXToolsClient(api_key, settings['dextools']['base_url'])
    
    try:
        print("   Tentando buscar holders com método corrigido...")
        holders = client.get_holders(test_chain, test_token, 10)
        
        if holders and len(holders) > 0 and 'total_holders' not in holders[0]:
            print(f"   ✅ SUCESSO! Encontrados {len(holders)} holders detalhados:")
            total_supply = 0
            for holder in holders:
                balance = float(holder.get('balance', 0))
                total_supply += balance
            
            print(f"   📊 Análise de concentração:")
            for i, holder in enumerate(holders[:5], 1):
                balance = float(holder.get('balance', 0))
                percentage = (balance / total_supply * 100) if total_supply > 0 else 0
                address = holder.get('address', 'N/A')
                print(f"   {i:2d}. {address[:10]}...{address[-6:]} - {percentage:.2f}%")
            
            top_5_total = sum(float(h.get('balance', 0)) for h in holders[:5])
            top_10_total = sum(float(h.get('balance', 0)) for h in holders[:10])
            concentration_5 = (top_5_total / total_supply * 100) if total_supply > 0 else 0
            concentration_10 = (top_10_total / total_supply * 100) if total_supply > 0 else 0
            
            print(f"\n   📈 CONCENTRAÇÃO:")
            print(f"   • Top 5 holders:  {concentration_5:.2f}% do supply")
            print(f"   • Top 10 holders: {concentration_10:.2f}% do supply")
            
        else:
            print(f"   ⚠️  Apenas dados básicos: {holders}")
            
    except Exception as e:
        print(f"   ❌ Erro no cliente: {e}")
    
    # Teste 4: Info detalhada do token
    print("\n4️⃣ Verificando dados disponíveis no /info...")
    info_url = f"{base_url}/token/{test_chain}/{test_token}/info"
    
    try:
        response = requests.get(info_url, headers=headers)
        if response.status_code == 200:
            info = response.json().get('data', {})
            print(f"   Holders total: {info.get('holders', 'N/A')}")
            print(f"   Market Cap: ${info.get('mcap', 0):,.2f}")
            print(f"   Supply: {info.get('totalSupply', 'N/A')}")
            print(f"   Transações: {info.get('transactions', 'N/A')}")
    except Exception as e:
        print(f"   ❌ Erro ao buscar info: {e}")

if __name__ == "__main__":
    test_holders_endpoints()