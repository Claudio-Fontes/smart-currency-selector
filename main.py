#!/usr/bin/env python3

import sys
import argparse
from dotenv import load_dotenv
from src.client import DEXToolsClient
from src.config import load_settings
from src.config.settings import validate_settings

load_dotenv()

def main():
    parser = argparse.ArgumentParser(description="Smart Currency Selector - DEXTools Analysis")
    parser.add_argument("token", nargs="?", help="Token address to analyze")
    parser.add_argument("-c", "--chain", default="solana", help="Blockchain (default: solana)")
    parser.add_argument("-s", "--save", action="store_true", help="Save results to file")
    parser.add_argument("--no-interactive", action="store_true", help="Run without interactive prompts")
    
    args = parser.parse_args()
    
    print("🚀 Smart Currency Selector - DEXTools Analysis")
    print("=" * 50)
    
    # Carregar configurações
    settings = load_settings()
    
    if not validate_settings(settings):
        return
    
    # Inicializar cliente
    client = DEXToolsClient(
        settings['dextools']['api_key'],
        settings['dextools']['base_url']
    )
    
    # Mapear chains para nomes corretos da API
    chain_mapping = {
        "eth": "ether", 
        "ethereum": "ether",
        "bsc": "bsc",
        "binance": "bsc", 
        "polygon": "polygon",
        "arbitrum": "arbitrum",
        "avalanche": "avalanche",
        "solana": "solana"
    }
    
    try:
        # Determinar chain
        chain = chain_mapping.get(args.chain.lower(), args.chain.lower())
        
        # Determinar token address
        token_address = args.token
        
        if not token_address and not args.no_interactive:
            # Modo interativo
            print("\nBlockchains disponíveis:")
            for key, value in chain_mapping.items():
                print(f"  - {key} ({value})")
            
            chain_input = input(f"\nBlockchain (default: solana): ").strip().lower()
            if chain_input:
                chain = chain_mapping.get(chain_input, chain_input)
            
            token_address = input(f"\nDigite o endereço do token na {chain.upper()}: ").strip()
        
        if not token_address:
            print("❌ Endereço do token é obrigatório.")
            print("Uso: python main.py <token_address> [-c chain] [-s]")
            print("Exemplo: python main.py egy3LC9ndbxo8LzL8W3s8FzwS3H6gT7t73uUP2Mpump -c solana")
            return
        
        print(f"\n🔍 Iniciando análise completa do token...")
        print(f"   Blockchain: {chain.upper()}")
        print(f"   Token: {token_address}")
        
        # Executa análise completa
        result = client.complete_analysis(chain, token_address)
        
        print("\n✅ Análise concluída!")
        
        # Salvar resultados
        if args.save or (not args.no_interactive and input("\nDeseja salvar os resultados em arquivo? (s/n): ").strip().lower() in ['s', 'sim', 'y', 'yes']):
            filename = f"analysis_{chain}_{token_address[-8:]}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"Análise DEXTools - {chain.upper()} - {token_address}\n")
                f.write("=" * 60 + "\n\n")
                
                f.write("SEGURANÇA:\n")
                for issue in result['security_issues']:
                    f.write(f"  {issue}\n")
                
                f.write(f"\nMÉTRICAS:\n")
                f.write(f"  Preço: ${result['metrics']['price_usd']:.8f}\n")
                f.write(f"  Variação 24h: {result['metrics']['price_change_24h']:.2f}%\n")
                f.write(f"  Market Cap: ${result['metrics']['mcap']:,.2f}\n")
                f.write(f"  Liquidez: ${result['metrics']['liquidity_usd']:,.2f}\n")
                f.write(f"  Volume 24h: ${result['metrics']['volume_24h_usd']:,.2f}\n")
                f.write(f"  Holders: {result['metrics']['holders_count']}\n")
                
                f.write(f"\nTENDÊNCIA: {result['trend']}\n")
                f.write(f"\nHOLDERS: {result['holders'].get('total_holders', 'N/A')}\n")
            
            print(f"📄 Resultados salvos em: {filename}")
    
    except KeyboardInterrupt:
        print("\n\n👋 Análise cancelada pelo usuário.")
    except Exception as e:
        print(f"\n❌ Erro durante a análise: {e}")

if __name__ == "__main__":
    main()