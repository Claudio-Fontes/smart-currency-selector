#!/usr/bin/env python3

import sys
import os
import requests
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_api_endpoint_with_taxes():
    """Test the API endpoint to see if tax data is being returned"""
    
    print("🔍 Teste da API do Backend - Endpoint de Análise com Taxas")
    print("=" * 65)
    
    # API endpoint local (o backend está rodando na porta 8000 segundo o log)
    base_url = "http://localhost:8000"
    
    # Token de teste
    test_token = "egy3LC9ndbxo8LzL8W3s8FzwS3H6gT7t73uUP2Mpump"  # DWOG token da Solana
    
    print(f"🎯 Testando token: {test_token}")
    print(f"📡 URL: {base_url}/api/token/{test_token}")
    
    try:
        # Fazer requisição para o endpoint
        response = requests.get(f"{base_url}/api/token/{test_token}")
        
        print(f"\n📊 Status da resposta: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"✅ Sucesso! Dados recebidos.")
            
            # Verificar se os campos de auditoria e taxas estão presentes
            token_data = data.get('data', {})
            
            print(f"\n🔍 ESTRUTURA DOS DADOS:")
            print(f"   success: {data.get('success')}")
            print(f"   tokenAddress: {data.get('tokenAddress')}")
            
            # Verificar dados básicos
            info = token_data.get('info', {})
            print(f"\n📋 INFO:")
            print(f"   name: {info.get('name')}")
            print(f"   symbol: {info.get('symbol')}")
            
            # Verificar dados de auditoria
            audit = token_data.get('audit', {})
            print(f"\n🔍 AUDIT DATA:")
            if audit:
                print(f"   is_honeypot: {audit.get('is_honeypot')}")
                print(f"   is_open_source: {audit.get('is_open_source')}")
                print(f"   is_contract_renounced: {audit.get('is_contract_renounced')}")
                print(f"   buy_tax: {audit.get('buy_tax')}")
                print(f"   sell_tax: {audit.get('sell_tax')}")
                print(f"   updated_at: {audit.get('updated_at')}")
            else:
                print("   ❌ Nenhum dado de auditoria encontrado")
            
            # Verificar dados de análise de taxas
            tax_analysis = token_data.get('tax_analysis', {})
            print(f"\n💰 TAX ANALYSIS DATA:")
            if tax_analysis:
                buy_info = tax_analysis.get('buy_tax_info', {})
                sell_info = tax_analysis.get('sell_tax_info', {})
                
                print(f"   buy_tax_info:")
                print(f"     min_percent: {buy_info.get('min_percent')}")
                print(f"     max_percent: {buy_info.get('max_percent')}")
                print(f"     status: {buy_info.get('status')}")
                print(f"     assessment: {buy_info.get('assessment')}")
                
                print(f"   sell_tax_info:")
                print(f"     min_percent: {sell_info.get('min_percent')}")
                print(f"     max_percent: {sell_info.get('max_percent')}")  
                print(f"     status: {sell_info.get('status')}")
                print(f"     assessment: {sell_info.get('assessment')}")
                
                print(f"   overall_assessment: {tax_analysis.get('overall_assessment')}")
                print(f"   is_honeypot: {tax_analysis.get('is_honeypot')}")
                print(f"   contract_renounced: {tax_analysis.get('contract_renounced')}")
            else:
                print("   ❌ Nenhum dado de análise de taxas encontrado")
            
            # Salvar resposta completa em arquivo para debug
            with open('api_response_debug.json', 'w') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Resposta completa salva em 'api_response_debug.json'")
            
            # Resumo
            has_audit = bool(audit and any(audit.values()))
            has_tax_analysis = bool(tax_analysis and any(tax_analysis.values()))
            
            print(f"\n📈 RESUMO DA INTEGRAÇÃO:")
            print(f"   ✅ API respondendo: Sim")
            print(f"   {'✅' if has_audit else '❌'} Dados de auditoria: {'Sim' if has_audit else 'Não'}")
            print(f"   {'✅' if has_tax_analysis else '❌'} Análise de taxas: {'Sim' if has_tax_analysis else 'Não'}")
            
            if has_audit and has_tax_analysis:
                print(f"\n🎉 SUCESSO COMPLETO! As informações de taxas estão sendo retornadas pela API.")
                print(f"📱 Os dados devem aparecer no frontend no painel de detalhes.")
            else:
                print(f"\n⚠️  INTEGRAÇÃO PARCIAL - alguns dados podem não estar disponíveis.")
                
        else:
            print(f"❌ Erro na API: {response.status_code}")
            print(f"Resposta: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Erro de conexão! O backend não está rodando em {base_url}")
        print(f"💡 Certifique-se de que o servidor Flask está ativo na porta 5000")
        
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")

if __name__ == "__main__":
    test_api_endpoint_with_taxes()