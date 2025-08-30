#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from src.client import DEXToolsClient
from src.config import load_settings

load_dotenv()

def test_complete_analysis_with_taxes():
    print("🔍 Teste da Análise Completa com Taxas")
    print("=" * 60)
    
    settings = load_settings()
    
    if not settings['dextools']['api_key']:
        print("❌ API key não configurada")
        return
    
    client = DEXToolsClient(
        settings['dextools']['api_key'],
        settings['dextools']['base_url']
    )
    
    # Token para teste - DEXT tem dados de auditoria
    test_chain = "ether"
    test_token = "0xfb7b4564402e5500db5bb6d63ae671302777c75a"
    
    print(f"Testando análise completa com token DEXT")
    
    try:
        # Executa análise completa (inclui agora as taxas)
        result = client.complete_analysis(test_chain, test_token)
        
        print(f"\n" + "="*60)
        print(f"RESUMO ESTRUTURADO DOS DADOS:")
        print(f"="*60)
        
        # Dados de taxas estruturados
        if 'tax_analysis' in result:
            tax_data = result['tax_analysis']
            print(f"\n💰 RESUMO FISCAL:")
            print(f"   Buy Tax: {tax_data['buy_tax_info']['min_percent']}% - {tax_data['buy_tax_info']['max_percent']}%")
            print(f"   Sell Tax: {tax_data['sell_tax_info']['min_percent']}% - {tax_data['sell_tax_info']['max_percent']}%")
            print(f"   Status Geral: {tax_data['overall_assessment']}")
            
            print(f"\n🔒 SEGURANÇA CONTRATUAL:")
            print(f"   Honeypot: {tax_data['is_honeypot']}")
            print(f"   Contrato Renunciado: {tax_data['contract_renounced']}")
            print(f"   Slippage Modificável: {tax_data['slippage_modifiable']}")
            
            # Cálculo de score de risco fiscal
            buy_max = tax_data['buy_tax_info']['max_percent'] or 0
            sell_max = tax_data['sell_tax_info']['max_percent'] or 0
            total_tax = buy_max + sell_max
            
            print(f"\n📊 SCORE DE RISCO FISCAL:")
            if total_tax == 0:
                print(f"   🟢 EXCELENTE (0% taxas) - Ideal para trading")
            elif total_tax <= 5:
                print(f"   🟡 BOM ({total_tax}% taxas) - Aceitável para DeFi")
            elif total_tax <= 15:
                print(f"   🟠 MODERADO ({total_tax}% taxas) - Cuidado com custos")
            elif total_tax <= 30:
                print(f"   🔴 ALTO ({total_tax}% taxas) - Evite se possível")
            else:
                print(f"   ⚫ EXTREMO ({total_tax}% taxas) - POSSÍVEL SCAM")
        
        print(f"\n✅ Análise completa finalizada com sucesso!")
        print(f"📋 As informações de taxas agora estão integradas no painel de detalhes.")
        
    except Exception as e:
        print(f"❌ Erro na análise completa: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_complete_analysis_with_taxes()