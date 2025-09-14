#!/usr/bin/env python3
"""
Inicia o monitor com logs detalhados no console
"""

import os
import sys
import time
import logging
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# Configurar logging LIMPO para reduzir spam
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',  # Formato mais limpo
    handlers=[
        logging.StreamHandler(sys.stdout),  # Mostra no console
        logging.FileHandler('monitor_trades.log')  # Salva em arquivo
    ]
)

# Configurar loggers específicos para reduzir spam
logging.getLogger('trade.utils.solana_client').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('requests').setLevel(logging.WARNING)
logging.getLogger('websockets').setLevel(logging.WARNING)

print("✅ Monitor iniciado com logging limpo - reduzido spam de consultas de saldo")

from trade.services.sell_service import sell_service
from trade.database.connection import TradeDatabase

logger = logging.getLogger(__name__)

def monitor_loop():
    """Loop principal de monitoramento"""
    
    print("="*80)
    print("🤖 MONITOR DE VENDAS AUTOMÁTICAS")
    print("="*80)
    print(f"📅 Iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("📊 Configurações:")
    print("   - Profit Target: +20%")
    print("   - Stop Loss: -10%")
    print("   - Intervalo: 30 segundos")
    print("="*80)
    print("\n⚡ Pressione Ctrl+C para parar\n")
    
    db = TradeDatabase()
    
    while True:
        try:
            print(f"\n{'='*60}")
            print(f"⏰ Ciclo: {datetime.now().strftime('%H:%M:%S')}")
            print(f"{'='*60}")
            
            # Mostrar trades abertas
            with db.get_cursor() as cursor:
                cursor.execute("""
                    SELECT id, token_address, token_symbol, buy_price, buy_amount, buy_time
                    FROM trades 
                    WHERE status = 'OPEN'
                    ORDER BY buy_time DESC
                """)
                open_trades = cursor.fetchall()
                
                if open_trades:
                    print(f"\n📈 {len(open_trades)} trades abertas:")
                    for trade in open_trades:
                        elapsed = datetime.now() - trade['buy_time']
                        minutes = int(elapsed.total_seconds() / 60)
                        print(f"   #{trade['id']} {trade['token_symbol']} - Comprado há {minutes} minutos")
                else:
                    print("\n✅ Nenhuma trade aberta")
            
            # Verificar trades para venda
            print("\n🔍 Verificando condições de venda...")
            trades_to_sell = sell_service.check_open_trades_for_sell()
            
            if trades_to_sell:
                print(f"🎯 {len(trades_to_sell)} trades prontas para venda!")
                
                for trade_info in trades_to_sell:
                    trade = trade_info['trade']
                    print(f"\n💰 VENDENDO: {trade['token_symbol']}")
                    print(f"   Motivo: {trade_info['sell_reason']}")
                    print(f"   Variação: {trade_info['price_change_pct']:+.2f}%")
                    
                    # Executar venda
                    result = sell_service.execute_sell(trade_info)
                    
                    if result:
                        print(f"   ✅ VENDA EXECUTADA!")
                        print(f"   P&L: {result['profit_loss_pct']:+.2f}%")
                        print(f"   TX: {result.get('transaction_hash', 'N/A')}")
                    else:
                        print(f"   ❌ ERRO NA VENDA")
            else:
                print("   Nenhuma trade atende critérios de venda ainda")
                
                # Mostrar variação atual de cada trade
                from backend.services.dextools_service import DEXToolsService
                dextools = DEXToolsService()
                
                print("\n📊 Variação atual das trades:")
                for trade in open_trades:
                    try:
                        token_info = dextools.get_token_price(trade['token_address'])
                        if token_info and token_info.get('success'):
                            current_price = float(token_info.get('data', {}).get('price', 0))
                            if current_price > 0:
                                buy_price = float(trade['buy_price'])
                                variation = ((current_price - buy_price) / buy_price) * 100
                                
                                # Emoji baseado na variação
                                if variation > 0:
                                    emoji = "📈"
                                elif variation < 0:
                                    emoji = "📉"
                                else:
                                    emoji = "➡️"
                                
                                print(f"   {emoji} {trade['token_symbol']}: {variation:+.2f}%")
                                
                                # Avisar quando está próximo dos limites
                                if variation >= 15:
                                    print(f"      ⚡ Próximo do PROFIT TARGET (+20%)")
                                elif variation <= -7:
                                    print(f"      ⚠️ Próximo do STOP LOSS (-10%)")
                    except Exception as e:
                        print(f"   ❌ Erro ao buscar preço de {trade['token_symbol']}: {e}")
            
            print(f"\n💤 Aguardando 30 segundos...")
            time.sleep(30)
            
        except KeyboardInterrupt:
            print("\n\n🛑 Monitor parado pelo usuário")
            break
        except Exception as e:
            print(f"\n❌ Erro no monitor: {e}")
            print("Reiniciando em 10 segundos...")
            time.sleep(10)

if __name__ == "__main__":
    monitor_loop()