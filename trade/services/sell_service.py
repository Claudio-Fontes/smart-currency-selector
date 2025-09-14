#!/usr/bin/env python3
"""
Serviço de venda automática de tokens
Monitora preços e vende em duas situações:
- Lucro de 20% (take profit)
- Prejuízo de 10% (stop loss)
"""

import os
import logging
from decimal import Decimal
from datetime import datetime
from typing import Dict, List, Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from trade.database.connection import TradeDatabase

logger = logging.getLogger(__name__)

class SellService:
    def __init__(self):
        self.db = TradeDatabase()
        self.config = self._load_config()
        
    def _load_config(self) -> Dict:
        """Carrega configurações do ambiente ou banco"""
        config = {}
        
        # Primeiro tenta carregar do ambiente
        profit_target = os.getenv('PROFIT_TARGET_PERCENTAGE')
        stop_loss = os.getenv('STOP_LOSS_PERCENTAGE')
        
        if profit_target and stop_loss:
            config['profit_target_percentage'] = profit_target
            config['stop_loss_percentage'] = stop_loss
        else:
            # Se não encontrar no ambiente, carrega do banco
            try:
                with self.db.get_cursor() as cursor:
                    cursor.execute("SELECT config_key, config_value FROM trade_config")
                    for row in cursor.fetchall():
                        config[row['config_key']] = row['config_value']
            except Exception as e:
                logger.error(f"Erro ao carregar config: {e}")
                
        # Defaults se nada foi configurado
        if 'profit_target_percentage' not in config:
            config['profit_target_percentage'] = '20'
        if 'stop_loss_percentage' not in config:
            config['stop_loss_percentage'] = '10'  # Mudado de 5 para 10
            
        return config
    
    def check_open_trades_for_sell(self) -> List[Dict]:
        """
        Verifica todas as trades abertas e retorna lista das que devem ser vendidas
        """
        trades_to_sell = []
        
        try:
            with self.db.get_cursor() as cursor:
                # Buscar todas as trades abertas para avaliação
                # Inclui: 1) Trades que já passaram do cooldown de 2h
                #         2) Trades em cooldown mas que podem ter atingido 50% de lucro
                #         3) NOVA REGRA: Trades com mais de 24 horas
                cursor.execute("""
                    SELECT 
                        t.id, t.token_address, t.token_symbol, t.token_name,
                        t.buy_price, t.buy_amount, t.buy_time,
                        CASE 
                            WHEN t.buy_time > NOW() - INTERVAL '2 hours' THEN true 
                            ELSE false 
                        END as in_cooldown,
                        CASE 
                            WHEN t.buy_time <= NOW() - INTERVAL '24 hours' THEN true 
                            ELSE false 
                        END as is_24h_old,
                        EXTRACT(EPOCH FROM (NOW() - t.buy_time))/3600 as hours_held
                    FROM trades t
                    WHERE t.status = 'OPEN'
                """)
                
                open_trades = cursor.fetchall()
                
                for trade in open_trades:
                    # NOVA REGRA: Verificar se tem mais de 24 horas
                    if trade.get('is_24h_old', False):
                        # Buscar preço atual mesmo assim para calcular P&L
                        current_price = self._get_current_token_price(trade['token_address'])
                        buy_price = float(trade['buy_price'])
                        price_change_pct = ((current_price - buy_price) / buy_price) * 100 if current_price else 0
                        
                        logger.info(f"⏰ Token {trade['token_symbol']} com {trade['hours_held']:.1f}h - VENDA FORÇADA (24H)")
                        logger.info(f"   Variação atual: {price_change_pct:+.2f}%")
                        
                        trades_to_sell.append({
                            'trade': trade,
                            'current_price': current_price if current_price else buy_price,
                            'price_change_pct': price_change_pct,
                            'sell_reason': 'TIMEOUT_24H'
                        })
                        continue  # Pula para o próximo token
                    
                    # Buscar preço atual do token
                    current_price = self._get_current_token_price(trade['token_address'])
                    
                    if current_price:
                        # Calcular variação percentual - converter Decimal para float
                        buy_price = float(trade['buy_price'])
                        price_change_pct = ((current_price - buy_price) / buy_price) * 100
                        
                        # CORREÇÃO: Log detalhado do cálculo de variação
                        logger.debug(f"Token {trade['token_symbol']}: Buy={buy_price:.10f}, Current={current_price:.10f}, Variação={price_change_pct:.2f}%")
                        
                        # Registrar monitoramento de preço
                        self._record_price_monitoring(trade['id'], trade['token_address'], 
                                                     current_price, price_change_pct)
                        
                        # Verificar condições de venda (incluindo exceção de cooldown)
                        sell_reason = self._should_sell(price_change_pct, trade.get('in_cooldown', False))
                        
                        if sell_reason:
                            trades_to_sell.append({
                                'trade': trade,
                                'current_price': current_price,
                                'price_change_pct': price_change_pct,
                                'sell_reason': sell_reason
                            })
                            
                            cooldown_info = " (EM COOLDOWN - EXCEÇÃO 50%)" if trade.get('in_cooldown') and price_change_pct >= 50 else ""
                            logger.info(f"📊 Token {trade['token_symbol']} marcado para venda{cooldown_info}")
                            logger.info(f"   Motivo: {sell_reason}")
                            logger.info(f"   Compra: ${buy_price:.10f}")
                            logger.info(f"   Atual: ${current_price:.10f}")
                            logger.info(f"   Variação: {price_change_pct:+.2f}%")
                
                return trades_to_sell
                
        except Exception as e:
            logger.error(f"Erro ao verificar trades: {e}")
            return []
    
    def _should_sell(self, price_change_pct: float, in_cooldown: bool = False) -> Optional[str]:
        """
        Determina se deve vender baseado na variação de preço
        
        Args:
            price_change_pct: Variação percentual do preço
            in_cooldown: Se a trade está em cooldown de 2h
        
        Returns:
            'PROFIT_TARGET' se atingiu lucro alvo normal (20%)
            'MEGA_PROFIT' se atingiu 50% (exceção ao cooldown)
            'STOP_LOSS' se atingiu prejuízo máximo
            None se não deve vender
        """
        profit_target = float(self.config.get('profit_target_percentage', '20'))
        stop_loss = float(self.config.get('stop_loss_percentage', '10'))
        mega_profit_threshold = 50.0  # Exceção ao cooldown
        
        # Log detalhado para debug
        logger.debug(f"Verificando venda - Variação: {price_change_pct:.2f}%, Target: {profit_target}%, Stop: -{stop_loss}%, Cooldown: {in_cooldown}")
        
        # NOVA REGRA: EXCEÇÃO - 50% de lucro vende SEMPRE (mesmo em cooldown)
        if price_change_pct >= mega_profit_threshold:
            if in_cooldown:
                logger.info(f"🚀 MEGA PROFIT (EXCEÇÃO COOLDOWN) atingido: {price_change_pct:.2f}% >= {mega_profit_threshold}%")
            else:
                logger.info(f"🚀 MEGA PROFIT atingido: {price_change_pct:.2f}% >= {mega_profit_threshold}%")
            return 'MEGA_PROFIT'
        
        # Durante cooldown, só vende com 50% ou mais (já verificado acima)
        if in_cooldown:
            logger.debug(f"Token em cooldown - só vende com 50%+. Atual: {price_change_pct:.2f}%")
            return None
        
        # Fora do cooldown: regras normais
        # Verificar se atingiu o lucro alvo normal (20% ou mais)
        if price_change_pct >= profit_target:
            logger.info(f"🎯 PROFIT TARGET atingido: {price_change_pct:.2f}% >= {profit_target}%")
            return 'PROFIT_TARGET'
        # Verificar se atingiu stop loss (-10% ou menos)
        elif price_change_pct <= -stop_loss:
            logger.info(f"🛑 STOP LOSS atingido: {price_change_pct:.2f}% <= -{stop_loss}%")
            return 'STOP_LOSS'
        
        return None
    
    def execute_sell(self, trade_info: Dict) -> Optional[Dict]:
        """
        Executa a venda do token
        
        Args:
            trade_info: Dict contendo trade, current_price, price_change_pct, sell_reason
        """
        trade = trade_info['trade']
        current_price = trade_info['current_price']
        sell_reason = trade_info['sell_reason']
        
        try:
            # Consultar saldo REAL da carteira primeiro
            from trade.utils.solana_client import SolanaTrader
            trader = SolanaTrader()
            real_balance = trader.get_token_balance(trade['token_address'])
            
            logger.info(f"📊 Análise de quantidade para venda:")
            logger.info(f"   Token: {trade['token_symbol']}")
            logger.info(f"   Token Address: {trade['token_address']}")
            logger.info(f"   Saldo real na carteira: {real_balance:.10f} tokens (UI)")
            
            if real_balance <= 0:
                logger.error(f"❌ Saldo insuficiente na carteira: {real_balance}")
                return None
            
            # CORREÇÃO: Vender apenas a quantidade comprada nesta trade específica
            buy_amount_original = float(trade['buy_amount'])
            buy_price = float(trade['buy_price'])
            token_decimals = trade.get('token_decimals', 9)
            
            logger.info(f"   Quantidade no banco: {buy_amount_original:.10f} tokens (UI)")
            logger.info(f"   Decimais do token: {token_decimals}")
            
            # CRÍTICO: Usar saldo REAL da carteira com máxima precisão
            # Converter com Decimal para evitar perda de precisão
            from decimal import Decimal, getcontext
            getcontext().prec = 18
            
            # 🎯 USAR 99.5% do saldo para evitar problemas de precisão no Jupiter
            sell_amount = real_balance * 0.995  # 99.5% para margem de segurança

            logger.info(f"   🎯 Quantidade a vender: {sell_amount:.10f} tokens (99.5% do saldo real)")
            logger.info(f"   📊 Conversão para RAW: {int(Decimal(str(sell_amount)) * Decimal(str(10 ** token_decimals))):,}")
            logger.info(f"   ⚠️  IMPORTANTE: Vendendo 99.5% do saldo para evitar erros de precisão Jupiter")
            
            # CORREÇÃO: Cálculo correto de P&L baseado na quantidade que está sendo vendida
            buy_total_original = buy_price * buy_amount_original
            sell_total = current_price * sell_amount
            
            # Se vendendo quantidade parcial, ajustar o custo proporcional
            if sell_amount < buy_amount_original:
                # Custo proporcional à quantidade vendida
                buy_cost_proportional = buy_price * sell_amount
                profit_loss = sell_total - buy_cost_proportional
                profit_loss_pct = ((sell_total - buy_cost_proportional) / buy_cost_proportional) * 100
            else:
                # Vendendo quantidade total original
                profit_loss = sell_total - buy_total_original
                profit_loss_pct = ((sell_total - buy_total_original) / buy_total_original) * 100
            
            logger.info(f"💰 Executando venda:")
            logger.info(f"   Token: {trade['token_symbol']}")
            logger.info(f"   Saldo original: {buy_amount_original:,.0f} tokens")
            logger.info(f"   Saldo real: {sell_amount:,.6f} tokens")
            logger.info(f"   Preço atual: ${current_price:.8f}")
            logger.info(f"   P&L: ${profit_loss:.2f} ({profit_loss_pct:+.2f}%)")
            
            # Executar transação de venda REAL na blockchain com decimais do banco
            token_decimals = trade.get('token_decimals', 9)  # Usar decimais do banco
            logger.info(f"🔢 Usando token_decimals do banco: {token_decimals}")
            
            # NOVA FUNCIONALIDADE: Verificar se token teve problemas de slippage antes
            from trade.utils.solana_client import SolanaTrader
            trader_check = SolanaTrader()
            if trade['token_address'] in trader_check.high_volatility_tokens:
                logger.warning(f"⚠️ Token {trade['token_symbol']} está na lista de alta volatilidade")
                logger.warning(f"   Será usado slippage de {trader_check.high_volatility_slippage_bps} BPS")
            
            transaction_hash = self._execute_real_sell_transaction(
                trade['token_address'],
                sell_amount,
                current_price,
                token_decimals  # CRÍTICO: Passar decimais para venda correta
            )
            
            # CRÍTICO: Só atualizar para CLOSED se a venda foi executada com sucesso
            if not transaction_hash:
                logger.error(f"❌ Venda não executada - mantendo posição OPEN")
                return None
            
            # Atualizar registro no banco APENAS se temos um hash válido
            success = self._record_sell_transaction(
                trade_id=trade['id'],
                sell_price=current_price,
                sell_amount=sell_amount,
                transaction_hash=transaction_hash,
                sell_reason=sell_reason,
                profit_loss=profit_loss,
                profit_loss_pct=profit_loss_pct
            )
            
            if success:
                logger.info(f"✅ Venda registrada com sucesso!")
                
                # Enviar notificação
                self._send_sell_notification(
                    trade, current_price, sell_reason, 
                    profit_loss, profit_loss_pct
                )
                
                return {
                    'trade_id': trade['id'],
                    'token_address': trade['token_address'],
                    'symbol': trade['token_symbol'],
                    'sell_price': current_price,
                    'sell_amount': sell_amount,
                    'profit_loss': profit_loss,
                    'profit_loss_pct': profit_loss_pct,
                    'sell_reason': sell_reason,
                    'transaction_hash': transaction_hash
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Erro ao executar venda: {e}")
            return None
    
    def _record_sell_transaction(self, trade_id: int, sell_price: float, sell_amount: float,
                                 transaction_hash: str, sell_reason: str, 
                                 profit_loss: float, profit_loss_pct: float) -> bool:
        """Registra a transação de venda no banco"""
        try:
            with self.db.get_cursor() as cursor:
                # Primeiro, buscar informações do trade
                cursor.execute("""
                    SELECT token_address, token_symbol 
                    FROM trades 
                    WHERE id = %s
                """, (trade_id,))
                
                trade_info = cursor.fetchone()
                
                cursor.execute("""
                    UPDATE trades SET
                        sell_price = %s,
                        sell_amount = %s,
                        sell_transaction_hash = %s,
                        sell_time = NOW(),
                        sell_reason = %s,
                        profit_loss_amount = %s,
                        profit_loss_percentage = %s,
                        status = 'CLOSED',
                        updated_at = NOW()
                    WHERE id = %s
                """, (
                    sell_price, sell_amount, transaction_hash,
                    sell_reason, profit_loss, profit_loss_pct,
                    trade_id
                ))
                
                # Se foi stop loss, adicionar à blacklist
                if sell_reason == 'STOP_LOSS' and profit_loss_pct <= -10:
                    try:
                        cursor.execute("""
                            INSERT INTO token_blacklist (token_address, token_symbol, reason, loss_percentage, trade_id)
                            VALUES (%s, %s, %s, %s, %s)
                            ON CONFLICT (token_address) 
                            DO UPDATE SET 
                                loss_percentage = LEAST(token_blacklist.loss_percentage, EXCLUDED.loss_percentage),
                                trade_id = EXCLUDED.trade_id,
                                blacklisted_at = CURRENT_TIMESTAMP
                        """, (
                            trade_info['token_address'],
                            trade_info['token_symbol'],
                            'Stop loss triggered',
                            profit_loss_pct,
                            trade_id
                        ))
                        logger.warning(f"🚫 Token {trade_info['token_symbol']} adicionado à blacklist (stop loss: {profit_loss_pct:.2f}%)")
                    except Exception as e:
                        logger.error(f"Erro ao adicionar à blacklist: {e}")
                
                return True
                
        except Exception as e:
            logger.error(f"Erro ao registrar venda: {e}")
            return False
    
    def _record_price_monitoring(self, trade_id: int, token_address: str, 
                                 current_price: float, price_change_pct: float):
        """Registra monitoramento de preço"""
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO price_monitoring (
                        trade_id, token_address, current_price, price_change_percentage
                    ) VALUES (%s, %s, %s, %s)
                """, (trade_id, token_address, current_price, price_change_pct))
                
        except Exception as e:
            logger.error(f"Erro ao registrar monitoramento: {e}")
    
    def _get_current_token_price(self, token_address: str) -> Optional[float]:
        """
        Busca o preço atual do token
        """
        try:
            # Importar o serviço DEXTools
            from backend.services.dextools_service import DEXToolsService
            
            dextools = DEXToolsService()
            token_info = dextools.get_token_price(token_address)
            
            if token_info and token_info.get('success'):
                return float(token_info.get('data', {}).get('price', 0))
            
            return None
            
        except Exception as e:
            logger.error(f"Erro ao buscar preço do token {token_address}: {e}")
            return None
    
    def _execute_real_sell_transaction(self, token_address: str, amount: float, price: float, token_decimals: int = 9) -> Optional[str]:
        """
        Executa transação de venda REAL na blockchain
        """
        try:
            logger.info(f"🔥 EXECUTANDO VENDA REAL NA BLOCKCHAIN")
            logger.info(f"   Token: {token_address}")
            logger.info(f"   Quantidade: {amount:.4f}")
            
            # Importar cliente Solana
            from trade.utils.solana_client import SolanaTrader
            
            # Criar instância do trader
            trader = SolanaTrader()
            
            # Executar venda real usando Jupiter COM DECIMAIS CORRETOS
            tx_hash = trader.sell_tokens(token_address, amount, token_decimals=token_decimals)
            
            if tx_hash:
                logger.info(f"✅ VENDA REAL EXECUTADA!")
                logger.info(f"🔗 TX Hash: {tx_hash}")
                return tx_hash
            else:
                logger.error(f"❌ Falha na execução da venda real - mantendo posição OPEN")
                
                # Se falhou, verificar se deve adicionar token à lista de alta volatilidade
                trader = SolanaTrader()
                if token_address not in trader.high_volatility_tokens:
                    trader.add_token_to_high_volatility_list(
                        token_address, 
                        "Falha automática na venda - possível problema de slippage"
                    )
                    logger.warning(f"🔄 Token {token_address[:8]}... adicionado à lista para próximas tentativas")
                
                # NÃO fazer fallback para simulação - retornar None para manter OPEN
                return None
                
        except Exception as e:
            logger.error(f"❌ Erro na venda real: {e}")
            logger.error(f"❌ Mantendo posição OPEN devido ao erro")
            
            # Se erro contém 0x1788, adicionar à lista de alta volatilidade
            if '0x1788' in str(e):
                logger.error(f"🚨 ERRO 0x1788 DETECTADO NO SELL_SERVICE!")
                try:
                    from trade.utils.solana_client import SolanaTrader
                    trader = SolanaTrader()
                    trader.add_token_to_high_volatility_list(
                        token_address, 
                        f"Erro 0x1788 capturado: {str(e)[:100]}"
                    )
                except:
                    pass
            
            # NÃO fazer fallback para simulação - retornar None para manter OPEN
            return None
    
    def _simulate_sell_transaction(self, token_address: str, amount: float, price: float) -> str:
        """
        Simula uma transação de venda (fallback)
        """
        import hashlib
        import time
        
        data = f"SELL_{token_address}{amount}{price}{time.time()}"
        tx_hash = hashlib.sha256(data.encode()).hexdigest()
        
        logger.info(f"🎮 FALLBACK: Simulação de venda")
        logger.info(f"🎮 TX Hash simulado: {tx_hash}")
        
        return tx_hash
    
    def _send_sell_notification(self, trade: Dict, sell_price: float, sell_reason: str,
                                profit_loss: float, profit_loss_pct: float):
        """Envia notificação de venda via Telegram"""
        try:
            from backend.services.telegram_notifier import telegram_notifier
            
            # Emoji baseado no resultado
            if profit_loss > 0:
                result_emoji = "✅"
                result_text = "LUCRO"
            else:
                result_emoji = "🔴"
                result_text = "PREJUÍZO"
            
            # Emoji e texto baseado no motivo
            if sell_reason == "PROFIT_TARGET":
                reason_emoji = "🎯"
                reason_text = "Meta de lucro atingida"
            elif sell_reason == "MEGA_PROFIT":
                reason_emoji = "🚀"
                reason_text = "MEGA lucro (50%+)"
            elif sell_reason == "STOP_LOSS":
                reason_emoji = "🛑"
                reason_text = "Stop loss acionado"
            elif sell_reason == "TIMEOUT_24H":
                reason_emoji = "⏰"
                reason_text = "Timeout 24 horas"
            else:
                reason_emoji = "📊"
                reason_text = sell_reason
            
            message = f"""{result_emoji} <b>VENDA EXECUTADA - {result_text}!</b>

🪙 Token: <b>{trade['token_symbol']}</b>
📝 Nome: {trade['token_name']}

💰 <b>Resultado:</b>
   Compra: ${trade['buy_price']:.8f}
   Venda: ${sell_price:.8f}
   P&L: ${profit_loss:.2f} ({profit_loss_pct:+.2f}%)

{reason_emoji} Motivo: {reason_text}
🆔 Trade ID: #{trade['id']}

⏰ Duração: {self._calculate_trade_duration(trade['buy_time'])}

🤖 Sistema de Trading Automático v1.0"""
            
            telegram_notifier.send_notification(message, "TRADE_SELL")
            
        except Exception as e:
            logger.error(f"Erro ao enviar notificação: {e}")
    
    def _calculate_trade_duration(self, buy_time) -> str:
        """Calcula a duração da trade"""
        try:
            if isinstance(buy_time, str):
                buy_time = datetime.fromisoformat(buy_time)
            
            duration = datetime.now() - buy_time
            hours = int(duration.total_seconds() / 3600)
            minutes = int((duration.total_seconds() % 3600) / 60)
            
            if hours > 0:
                return f"{hours}h {minutes}min"
            else:
                return f"{minutes}min"
                
        except:
            return "N/A"

# Instância global
sell_service = SellService()