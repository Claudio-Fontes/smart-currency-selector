#!/usr/bin/env python3
"""
Daemon de Monitoramento Automático de Trading
Monitora continuamente:
- Trades abertas para vender (profit +20% ou stop loss -10%)
- Novas sugestões para comprar (score >= 80)
"""

import os
import sys
import time
import signal
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from trade.services.trade_monitor import TradeMonitor

# Flag para controle do daemon
running = True

def signal_handler(signum, frame):
    """Handler para parar o daemon graciosamente"""
    global running
    print("\n🛑 Recebido sinal de parada. Finalizando daemon...")
    running = False

# Registrar handlers de sinal
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def main():
    """Função principal do daemon"""
    print("=" * 80)
    print("🤖 DAEMON DE MONITORAMENTO AUTOMÁTICO")
    print("=" * 80)
    print(f"🕐 Iniciado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    profit_target = os.getenv('PROFIT_TARGET_PERCENTAGE', '20')
    stop_loss = os.getenv('STOP_LOSS_PERCENTAGE', '10')
    
    print("📊 Configurações:")
    print(f"   - Profit Target: +{profit_target}%")
    print(f"   - Stop Loss: -{stop_loss}%")
    print("   - Intervalo: 60 segundos")
    print("   - Score mínimo para compra: 80")
    print("=" * 80)
    print("\n⚡ Pressione Ctrl+C para parar\n")
    
    # Criar instância do monitor
    monitor = TradeMonitor()
    
    # Verificar se trading automático está ativo
    from trade.database.connection import TradeDatabase
    db = TradeDatabase()
    
    with db.get_cursor() as cursor:
        cursor.execute("SELECT config_value FROM trade_config WHERE config_key = 'auto_trading_enabled'")
        config = cursor.fetchone()
        
        if not config or config['config_value'].lower() != 'true':
            print("❌ Auto-trading está DESATIVADO")
            print("Para ativar: UPDATE trade_config SET config_value = 'true' WHERE config_key = 'auto_trading_enabled'")
            return
    
    print("✅ Auto-trading está ATIVO")
    print("🚀 Iniciando monitoramento...\n")
    
    # Loop principal
    while running:
        try:
            print(f"\n{'='*60}")
            print(f"⏰ Ciclo: {datetime.now().strftime('%H:%M:%S')}")
            print(f"{'='*60}")
            
            # Verificar trades abertas para vender
            print("\n📈 Verificando trades abertas...")
            monitor._check_open_trades()
            
            # Verificar novas sugestões para comprar
            print("\n🔍 Verificando novas sugestões...")
            monitor._check_new_suggestions()
            
            # Mostrar estatísticas
            monitor._show_statistics()
            
            if running:
                print(f"\n💤 Aguardando 60 segundos para próximo ciclo...")
                print("   (Ctrl+C para parar)")
                
                # Sleep interruptível
                for i in range(60):
                    if not running:
                        break
                    time.sleep(1)
                    
        except KeyboardInterrupt:
            print("\n⚠️ Interrompido pelo usuário")
            break
        except Exception as e:
            print(f"\n❌ Erro no ciclo: {e}")
            import traceback
            traceback.print_exc()
            
            if running:
                print("⏳ Aguardando 10 segundos antes de tentar novamente...")
                time.sleep(10)
    
    print("\n" + "=" * 80)
    print("🛑 DAEMON FINALIZADO")
    print(f"🕐 Parado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

if __name__ == "__main__":
    main()