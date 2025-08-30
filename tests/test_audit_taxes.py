#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from src.client import DEXToolsClient
from src.config import load_settings

load_dotenv()

def test_audit_and_taxes():
    print("🔍 Teste do Endpoint de Auditoria e Análise de Taxas")
    print("=" * 60)
    
    settings = load_settings()
    
    if not settings['dextools']['api_key']:
        print("❌ API key não configurada")
        return
    
    client = DEXToolsClient(
        settings['dextools']['api_key'],
        settings['dextools']['base_url']
    )
    
    # Tokens de teste - vários tipos para verificar diferentes cenários
    test_tokens = [
        {"chain": "ether", "address": "0xfb7b4564402e5500db5bb6d63ae671302777c75a", "name": "DEXT"},
        {"chain": "ether", "address": "0xA0b86a33E6441e6fb7F8eE8CC331dD4B08b9e1d3", "name": "USDC"},  # Token padrão
        {"chain": "solana", "address": "egy3LC9ndbxo8LzL8W3s8FzwS3H6gT7t73uUP2Mpump", "name": "DWOG"},  # Meme token
    ]
    
    for token in test_tokens:
        print(f"\n{'='*50}")
        print(f"🧪 TESTANDO TOKEN: {token['name']} ({token['chain'].upper()})")
        print(f"📍 Endereço: {token['address']}")
        print(f"{'='*50}")
        
        try:
            # Teste 1: Dados brutos de auditoria
            print("\n1️⃣ Dados brutos de auditoria...")
            audit_data = client.get_token_audit(token['chain'], token['address'])
            
            print(f"   🔍 Open Source: {audit_data.get('is_open_source', 'N/A')}")
            print(f"   🍯 Honeypot: {audit_data.get('is_honeypot', 'N/A')}")
            print(f"   🏭 Mintable: {audit_data.get('is_mintable', 'N/A')}")
            print(f"   🎭 Proxy: {audit_data.get('is_proxy', 'N/A')}")
            print(f"   📊 Slippage Modificável: {audit_data.get('slippage_modifiable', 'N/A')}")
            print(f"   🚫 Blacklist: {audit_data.get('is_blacklisted', 'N/A')}")
            print(f"   🔐 Contrato Renunciado: {audit_data.get('is_contract_renounced', 'N/A')}")
            print(f"   ⚠️  Possível Scam: {audit_data.get('is_potentially_scam', 'N/A')}")
            
            # Teste 2: Análise específica de taxas
            print("\n2️⃣ Análise detalhada de taxas...")
            tax_analysis = client.analyze_token_taxes(token['chain'], token['address'])
            
            buy_info = tax_analysis.get('buy_tax_info', {})
            sell_info = tax_analysis.get('sell_tax_info', {})
            
            print(f"\n   💸 TAXAS DE COMPRA:")
            print(f"      Min: {buy_info.get('min_percent', 0)}%")
            print(f"      Max: {buy_info.get('max_percent', 0)}%") 
            print(f"      Status: {buy_info.get('status', 'N/A')}")
            print(f"      {buy_info.get('assessment', 'N/A')}")
            
            print(f"\n   💰 TAXAS DE VENDA:")
            print(f"      Min: {sell_info.get('min_percent', 0)}%")
            print(f"      Max: {sell_info.get('max_percent', 0)}%")
            print(f"      Status: {sell_info.get('status', 'N/A')}")
            print(f"      {sell_info.get('assessment', 'N/A')}")
            
            print(f"\n   📈 AVALIAÇÃO GERAL:")
            print(f"      {tax_analysis.get('overall_assessment', 'N/A')}")
            
            # Teste 3: Informações de segurança adicionais
            print(f"\n   🛡️ INFORMAÇÕES DE SEGURANÇA:")
            print(f"      Honeypot: {tax_analysis.get('is_honeypot', 'N/A')}")
            print(f"      Slippage Modificável: {tax_analysis.get('slippage_modifiable', 'N/A')}")
            print(f"      Contrato Renunciado: {tax_analysis.get('contract_renounced', 'N/A')}")
            
            audit_date = tax_analysis.get('audit_date', '')
            if audit_date:
                print(f"      Última Auditoria: {audit_date}")
            else:
                print(f"      Última Auditoria: Dados não disponíveis")
            
            # Resumo de risco baseado nas taxas
            buy_max = buy_info.get('max_percent', 0)
            sell_max = sell_info.get('max_percent', 0)
            total_tax = buy_max + sell_max
            
            print(f"\n   ⚖️ RESUMO DE RISCO FISCAL:")
            if total_tax == 0:
                print(f"      🟢 BAIXO RISCO - Sem taxas")
            elif total_tax <= 5:
                print(f"      🟡 RISCO MODERADO - Taxas baixas ({total_tax}%)")
            elif total_tax <= 15:
                print(f"      🟠 RISCO ELEVADO - Taxas moderadas ({total_tax}%)")
            elif total_tax <= 30:
                print(f"      🔴 ALTO RISCO - Taxas altas ({total_tax}%)")
            else:
                print(f"      ⚫ RISCO EXTREMO - Taxas suspeitas ({total_tax}%)")
                
        except Exception as e:
            print(f"\n❌ Erro ao testar token {token['name']}: {e}")
        
        print(f"\n{'_'*50}")
    
    print(f"\n✅ Teste concluído!")
    print(f"\n📋 LEGENDA DE INTERPRETAÇÃO:")
    print(f"   🟢 0-5%: Taxas normais para DeFi")
    print(f"   🟡 5-15%: Taxas altas mas ainda aceitáveis") 
    print(f"   🟠 15-30%: Taxas muito altas - cuidado")
    print(f"   🔴 30%+: Taxas suspeitas - possível scam")

if __name__ == "__main__":
    test_audit_and_taxes()