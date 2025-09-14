#!/usr/bin/env python3
"""
Monitor de Trading Automático
Monitora continuamente:
1. Novas sugestões para comprar (apenas primeira vez)
2. Trades abertas para vender (lucro 20% ou prejuízo 10%)
"""

import os
import logging
import time
import threading
from datetime import datetime
from typing import Dict, Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from trade.services.buy_service import buy_service
from trade.services.sell_service import sell_service
from trade.database.connection import TradeDatabase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TradeMonitor:
    def __init__(self):
        self.db = TradeDatabase()
        self.running = False
        self.monitor_thread = None
        self.config = self._load_config()
        
    def _load_config(self) -> Dict:
        """Carrega configurações do ambiente ou banco"""
        config = {}
        
        # Carregar parâmetros de trading do ambiente
        profit_target = os.getenv('PROFIT_TARGET_PERCENTAGE')
        stop_loss = os.getenv('STOP_LOSS_PERCENTAGE')
        
        if profit_target:
            config['profit_target_percentage'] = profit_target
        if stop_loss:
            config['stop_loss_percentage'] = stop_loss
            
        # Carregar outras configs do banco
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute("SELECT config_key, config_value FROM trade_config")
                for row in cursor.fetchall():
                    # Só sobrescreve se não veio do ambiente
                    if row['config_key'] not in config:
                        config[row['config_key']] = row['config_value']
        except Exception as e:
            logger.error(f"Erro ao carregar config: {e}")
            
        # Defaults
        if 'monitoring_interval_seconds' not in config:
            config['monitoring_interval_seconds'] = '30'  # Reduzido para execução mais rápida de stop loss
        if 'auto_trading_enabled' not in config:
            config['auto_trading_enabled'] = 'false'
        if 'profit_target_percentage' not in config:
            config['profit_target_percentage'] = '20'
        if 'stop_loss_percentage' not in config:
            config['stop_loss_percentage'] = '10'
            
        return config
    
    def start(self):
        """Inicia o monitoramento em thread separada"""
        if self.running:
            logger.warning("Monitor já está rodando")
            return
        
        if self.config.get('auto_trading_enabled', 'false').lower() != 'true':
            logger.warning("⚠️ Trading automático está DESABILITADO")
            logger.info("Para ativar: UPDATE trade_config SET config_value = 'true' WHERE config_key = 'auto_trading_enabled'")
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        logger.info("🚀 Monitor de trading iniciado!")
        logger.info(f"   Intervalo: {self.config.get('monitoring_interval_seconds', 60)} segundos")
        logger.info(f"   Profit Target: +{self.config.get('profit_target_percentage', 20)}%")
        logger.info(f"   Stop Loss: -{self.config.get('stop_loss_percentage', 10)}%")
        logger.info(f"   ❄️  Cooldown de venda: 2 horas após compra")
        logger.info(f"   🚀 Exceção cooldown: venda imediata com +50% lucro")
    
    def stop(self):
        """Para o monitoramento"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("🛑 Monitor de trading parado")
    
    def _monitor_loop(self):
        """Loop principal de monitoramento"""
        interval = int(self.config.get('monitoring_interval_seconds', '60'))
        
        while self.running:
            try:
                logger.info(f"\n{'='*60}")
                logger.info(f"⏰ Ciclo de monitoramento: {datetime.now().strftime('%H:%M:%S')}")
                logger.info(f"{'='*60}")
                
                # 1. Verificar novas sugestões para comprar
                self._check_new_suggestions()
                
                # 2. Verificar trades abertas para vender
                self._check_open_trades()
                
                # 3. Mostrar estatísticas
                self._show_statistics()
                
                # Aguardar próximo ciclo
                if self.running:
                    logger.info(f"💤 Aguardando {interval} segundos para próximo ciclo...")
                    time.sleep(interval)
                    
            except Exception as e:
                logger.error(f"Erro no ciclo de monitoramento: {e}")
                time.sleep(10)  # Aguardar um pouco em caso de erro
    
    def _check_new_suggestions(self):
        """Verifica novas sugestões de tokens para comprar"""
        try:
            logger.info("🔍 Verificando novas sugestões...")
            
            # Buscar sugestões recentes não compradas
            with self.db.get_cursor() as cursor:
                # CORREÇÃO: Buscar tokens sugeridos que não têm posição ABERTA
                # Permite recomprar tokens que já foram vendidos
                cursor.execute("""
                    SELECT DISTINCT ON (s.token_address)
                        s.id as suggestion_id,
                        s.token_address,
                        s.token_name,
                        s.token_symbol,
                        s.price_usd,
                        s.analysis_score
                    FROM suggested_tokens s
                    LEFT JOIN trades t ON s.token_address = t.token_address AND t.status = 'OPEN'
                    WHERE t.id IS NULL  -- Não tem posição ABERTA deste token
                    AND s.suggested_at > NOW() - INTERVAL '1 hour'  -- Sugestões da última hora
                    AND s.analysis_score >= 80  -- Score mínimo
                    AND NOT EXISTS (  -- Não foi comprado nos últimos 30 segundos (evita duplicação)
                        SELECT 1 FROM trades t2 
                        WHERE t2.token_address = s.token_address 
                        AND t2.buy_time > NOW() - INTERVAL '30 seconds'
                    )
                    -- NOVO: Cooldown após venda lucrativa (2 horas)
                    AND NOT EXISTS (  
                        SELECT 1 FROM trades t3 
                        WHERE t3.token_address = s.token_address 
                        AND t3.status IN ('SOLD', 'CLOSED')
                        AND t3.profit_loss_percentage > 0  -- Venda lucrativa
                        AND t3.sell_time > NOW() - INTERVAL '2 hours'  -- Últimas 2 horas
                    )
                    -- NOVO: Limite diário de trades por token (máximo 3)
                    AND (
                        SELECT COUNT(*) FROM trades t4 
                        WHERE t4.token_address = s.token_address 
                        AND t4.buy_time > CURRENT_DATE  -- Hoje
                    ) < 3
                    ORDER BY s.token_address, s.suggested_at DESC
                """)
                
                new_suggestions = cursor.fetchall()
                
                # NOVO: Verificar tokens bloqueados por cooldown/limite
                cursor.execute("""
                    SELECT DISTINCT s.token_symbol, s.token_address,
                           COUNT(t_today.id) as trades_today,
                           MAX(t_recent.sell_time) as last_sell
                    FROM suggested_tokens s
                    LEFT JOIN trades t_open ON s.token_address = t_open.token_address AND t_open.status = 'OPEN'
                    LEFT JOIN trades t_today ON s.token_address = t_today.token_address AND t_today.buy_time > CURRENT_DATE
                    LEFT JOIN trades t_recent ON s.token_address = t_recent.token_address 
                                               AND t_recent.status IN ('SOLD', 'CLOSED')
                                               AND t_recent.profit_loss_percentage > 0
                                               AND t_recent.sell_time > NOW() - INTERVAL '2 hours'
                    WHERE t_open.id IS NULL  -- Sem posição aberta
                    AND s.suggested_at > NOW() - INTERVAL '1 hour'
                    AND s.analysis_score >= 80
                    GROUP BY s.token_symbol, s.token_address
                    HAVING (
                        COUNT(t_today.id) >= 3  -- Limite diário atingido
                        OR MAX(t_recent.sell_time) IS NOT NULL  -- Em cooldown
                    )
                """)
                
                blocked_tokens = cursor.fetchall()
                for blocked in blocked_tokens:
                    if blocked['trades_today'] >= 3:
                        logger.info(f"   ⏸️ {blocked['token_symbol']} bloqueado: limite diário ({blocked['trades_today']}/3 trades)")
                    elif blocked['last_sell']:
                        logger.info(f"   ❄️ {blocked['token_symbol']} em cooldown: vendido há menos de 2h")

                if new_suggestions:
                    logger.info(f"   📊 {len(new_suggestions)} tokens sugeridos não comprados")
                    
                    for suggestion in new_suggestions:
                        logger.info(f"   🪙 {suggestion['token_symbol']} - Score: {suggestion['analysis_score']}")
                        
                        # Preparar dados para compra
                        token_data = {
                            'token_address': suggestion['token_address'],
                            'token_name': suggestion['token_name'],
                            'symbol': suggestion['token_symbol'],
                            'price_usd': suggestion['price_usd'],
                            'suggestion_id': suggestion['suggestion_id']
                        }
                        
                        # Executar compra com suggestion_id para evitar duplicação
                        result = buy_service.execute_buy(token_data, suggestion['suggestion_id'])
                        
                        if result:
                            logger.info(f"   ✅ Compra executada: {suggestion['token_symbol']}")
                        else:
                            logger.info(f"   ⏭️ Compra não executada: {suggestion['token_symbol']}")
                else:
                    logger.info("   ✅ Nenhuma nova sugestão para comprar")
                    
        except Exception as e:
            logger.error(f"Erro ao verificar sugestões: {e}")
    
    def _check_open_trades(self):
        """Verifica trades abertas para possível venda"""
        try:
            logger.info("📈 Verificando trades abertas...")
            
            # Buscar trades que devem ser vendidas
            trades_to_sell = sell_service.check_open_trades_for_sell()
            
            if trades_to_sell:
                logger.info(f"   🎯 {len(trades_to_sell)} trades marcadas para venda")
                
                for trade_info in trades_to_sell:
                    trade = trade_info['trade']
                    logger.info(f"   💰 Vendendo {trade['token_symbol']} - {trade_info['sell_reason']}")
                    
                    # Executar venda
                    result = sell_service.execute_sell(trade_info)
                    
                    if result:
                        logger.info(f"   ✅ Venda executada: {trade['token_symbol']} - P&L: {result['profit_loss_pct']:+.2f}%")
                    else:
                        logger.error(f"   ❌ Erro ao vender: {trade['token_symbol']}")
            else:
                # Mostrar status das trades abertas
                with self.db.get_cursor() as cursor:
                    cursor.execute("""
                        SELECT COUNT(*) as count FROM trades WHERE status = 'OPEN'
                    """)
                    open_count = cursor.fetchone()['count']
                    
                    if open_count > 0:
                        logger.info(f"   📊 {open_count} trades abertas (verificando condições de venda...)")
                        
                        # Mostrar detalhes das trades abertas
                        cursor.execute("""
                            SELECT 
                                t.token_symbol,
                                t.buy_price,
                                t.buy_time,
                                pm.current_price,
                                pm.price_change_percentage,
                                pm.monitored_at,
                                CASE 
                                    WHEN t.buy_time > NOW() - INTERVAL '2 hours' 
                                    THEN EXTRACT(EPOCH FROM (t.buy_time + INTERVAL '2 hours' - NOW()))/60
                                    ELSE 0 
                                END as cooldown_minutes
                            FROM trades t
                            LEFT JOIN LATERAL (
                                SELECT * FROM price_monitoring 
                                WHERE trade_id = t.id 
                                ORDER BY monitored_at DESC 
                                LIMIT 1
                            ) pm ON true
                            WHERE t.status = 'OPEN'
                            ORDER BY t.buy_time DESC
                        """)
                        
                        for trade in cursor.fetchall():
                            if trade['cooldown_minutes'] > 0:
                                # Trade em cooldown - mas pode ser vendável se tiver 50%+
                                cooldown_min = int(trade['cooldown_minutes'])
                                if trade['price_change_percentage'] is not None and trade['price_change_percentage'] >= 50:
                                    logger.info(f"      🚀 {trade['token_symbol']}: {trade['price_change_percentage']:+.2f}% (VENDÁVEL - EXCEÇÃO 50%)")
                                else:
                                    pct_info = f" ({trade['price_change_percentage']:+.1f}%)" if trade['price_change_percentage'] is not None else ""
                                    logger.info(f"      ❄️ {trade['token_symbol']}: cooldown {cooldown_min}min{pct_info}")
                            elif trade['price_change_percentage'] is not None:
                                # Trade vendável
                                emoji = "🟢" if trade['price_change_percentage'] > 0 else "🔴"
                                logger.info(f"      {emoji} {trade['token_symbol']}: {trade['price_change_percentage']:+.2f}% (vendável)")
                    else:
                        logger.info("   ✅ Nenhuma trade aberta")
                        
        except Exception as e:
            logger.error(f"Erro ao verificar trades abertas: {e}")
    
    def _show_statistics(self):
        """Mostra estatísticas de trading"""
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_trades,
                        COUNT(CASE WHEN status = 'OPEN' THEN 1 END) as open_trades,
                        COUNT(CASE WHEN status = 'CLOSED' THEN 1 END) as closed_trades,
                        COUNT(CASE WHEN profit_loss_percentage > 0 THEN 1 END) as winning_trades,
                        COUNT(CASE WHEN profit_loss_percentage < 0 THEN 1 END) as losing_trades,
                        AVG(CASE WHEN status = 'CLOSED' THEN profit_loss_percentage END) as avg_pnl,
                        SUM(CASE WHEN status = 'CLOSED' THEN profit_loss_amount END) as total_pnl
                    FROM trades
                """)
                
                stats = cursor.fetchone()
                
                if stats['total_trades'] > 0:
                    logger.info("\n📊 ESTATÍSTICAS:")
                    logger.info(f"   Total de trades: {stats['total_trades']}")
                    logger.info(f"   Abertas: {stats['open_trades']} | Fechadas: {stats['closed_trades']}")
                    
                    if stats['closed_trades'] > 0:
                        win_rate = (stats['winning_trades'] / stats['closed_trades']) * 100 if stats['closed_trades'] > 0 else 0
                        logger.info(f"   Win Rate: {win_rate:.1f}%")
                        logger.info(f"   P&L Médio: {stats['avg_pnl']:+.2f}%")
                        logger.info(f"   P&L Total: ${stats['total_pnl']:+.2f}")
                        
        except Exception as e:
            logger.error(f"Erro ao mostrar estatísticas: {e}")

# Instância global
trade_monitor = TradeMonitor()

if __name__ == "__main__":
    # Se executado diretamente, inicia o monitor
    logger.info("Iniciando monitor de trading...")
    
    monitor = TradeMonitor()
    monitor.start()
    
    try:
        # Manter o programa rodando
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("\nParando monitor...")
        monitor.stop()