#!/usr/bin/env python3
"""
Serviço de compra automática de tokens
Compra apenas na primeira vez que um token é sugerido
"""

import os
import logging
from decimal import Decimal
from datetime import datetime
from typing import Dict, Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from trade.database.connection import TradeDatabase
from trade.utils.solana_client import SolanaTrader

logger = logging.getLogger(__name__)

class BuyService:
    def __init__(self):
        self.db = TradeDatabase()
        self.trader = SolanaTrader()
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
        if 'auto_trading_enabled' not in config:
            config['auto_trading_enabled'] = 'false'
        if 'max_trade_amount_sol' not in config:
            config['max_trade_amount_sol'] = '0.1'
        if 'profit_target_percentage' not in config:
            config['profit_target_percentage'] = '20'
        if 'stop_loss_percentage' not in config:
            config['stop_loss_percentage'] = '10'  # Mudado de 5 para 10
            
        return config
    
    def should_buy_token(self, token_address: str) -> bool:
        """
        Verifica se deve comprar o token
        Retorna True apenas se:
        - Trading automático está ativo
        - Token não está na blacklist
        - Não tem posição ABERTA deste token (pode comprar novamente após vender)
        - Não foi comprado nos últimos 30 segundos (evita duplicação)
        """
        if self.config.get('auto_trading_enabled', 'false').lower() != 'true':
            logger.info(f"Trading automático desabilitado")
            return False
            
        try:
            with self.db.get_cursor() as cursor:
                # NOVO: Verificar se token está na blacklist
                cursor.execute("""
                    SELECT token_symbol, loss_percentage, blacklisted_at
                    FROM token_blacklist 
                    WHERE token_address = %s
                """, (token_address,))
                
                blacklisted = cursor.fetchone()
                if blacklisted:
                    logger.warning(f"🚫 Token {blacklisted['token_symbol']} está na BLACKLIST (perda de {blacklisted['loss_percentage']:.2f}% em {blacklisted['blacklisted_at']})")
                    return False
                
                # CORREÇÃO: Verificar se já existe trade ABERTA para este token
                cursor.execute("""
                    SELECT COUNT(*) as count
                    FROM trades 
                    WHERE token_address = %s
                    AND status = 'OPEN'
                """, (token_address,))
                
                result = cursor.fetchone()
                if result['count'] > 0:
                    logger.info(f"Token {token_address} já tem posição aberta")
                    return False
                
                # MELHORADO: Verificar se foi comprado nos últimos 2 minutos (evita duplicação)
                cursor.execute("""
                    SELECT COUNT(*) as recent_count, 
                           MAX(buy_time) as last_buy,
                           STRING_AGG(DISTINCT suggestion_id::text, ', ') as suggestion_ids
                    FROM trades 
                    WHERE token_address = %s
                    AND buy_time > NOW() - INTERVAL '2 minutes'
                """, (token_address,))
                
                recent = cursor.fetchone()
                if recent['recent_count'] > 0:
                    logger.warning(f"🚨 DUPLICAÇÃO DETECTADA - Token {token_address[:8]}...")
                    logger.warning(f"   Compras recentes: {recent['recent_count']}")
                    logger.warning(f"   Última compra: {recent['last_buy']}")
                    logger.warning(f"   Suggestion IDs: {recent['suggestion_ids']}")
                    logger.warning(f"   ⛔ BLOQUEANDO nova compra por 2 minutos")
                    return False
                    
                # Verificar quantas vezes já foi comprado e vendido
                cursor.execute("""
                    SELECT COUNT(*) as total_trades,
                           COUNT(CASE WHEN status = 'CLOSED' AND profit_loss_percentage > 0 THEN 1 END) as wins
                    FROM trades 
                    WHERE token_address = %s
                """, (token_address,))
                
                history = cursor.fetchone()
                if history['total_trades'] > 0:
                    logger.info(f"Token {token_address} já foi negociado {history['total_trades']}x (Wins: {history['wins']})")
                    
                return True
                
        except Exception as e:
            logger.error(f"Erro ao verificar token: {e}")
            return False
    
    def execute_buy(self, token_data: Dict, suggestion_id: str = None) -> Optional[Dict]:
        """
        Executa a compra do token com proteção anti-duplicação
        
        Args:
            token_data: Dados do token incluindo address, symbol, name, price
            suggestion_id: ID único da sugestão para evitar duplicação
            
        Returns:
            Dict com informações da trade ou None se falhou
        """
        token_address = token_data.get('token_address')
        
        if not token_address:
            logger.error("Token address não fornecido")
            return None
            
        # NOVA PROTEÇÃO: Verificar duplicação por suggestion_id ANTES de qualquer processamento
        if suggestion_id:
            try:
                with self.db.get_cursor() as cursor:
                    cursor.execute("""
                        SELECT id, buy_time, token_symbol
                        FROM trades 
                        WHERE suggestion_id = %s
                        ORDER BY buy_time DESC
                        LIMIT 5
                    """, (suggestion_id,))
                    
                    existing_trades = cursor.fetchall()
                    if existing_trades:
                        logger.warning(f"🚨 SUGGESTION_ID DUPLICADO: {suggestion_id}")
                        logger.warning(f"   Trades existentes com mesmo ID: {len(existing_trades)}")
                        for trade in existing_trades:
                            logger.warning(f"   - Trade ID {trade['id']}: {trade['token_symbol']} em {trade['buy_time']}")
                        logger.warning(f"   ⛔ BLOQUEANDO compra por suggestion_id duplicado")
                        return None
            except Exception as e:
                logger.error(f"Erro ao verificar suggestion_id: {e}")
                # Continua mesmo com erro na verificação
        
        # Verificar se deve comprar (verificações gerais)
        if not self.should_buy_token(token_address):
            return None
            
        try:
            # Preparar valores - REDUZIDO temporariamente para 0.01 SOL até corrigir problema de venda
            max_amount_sol = 0.01  # TEMPORÁRIO: Reduzido de 0.05 para minimizar riscos
            
            # CORREÇÃO CRÍTICA: Buscar preço REAL do mercado no momento da compra
            logger.info(f"🔍 Buscando preço atual do mercado para {token_data.get('symbol')}...")
            current_price = self._get_current_token_price(token_address)
            
            if not current_price or current_price <= 0:
                logger.error(f"❌ Não foi possível obter preço atual do token {token_data.get('symbol')}")
                logger.info(f"   Usando preço da sugestão como fallback: ${token_data.get('price_usd', 0)}")
                current_price = float(token_data.get('price_usd', 0))
                
                if current_price <= 0:
                    logger.error("❌ Preço inválido - cancelando compra")
                    return None
            
            logger.info(f"💰 Preço real do mercado: ${current_price:.8f}")
            logger.info(f"Comprando {token_data.get('symbol')} por {max_amount_sol} SOL")
            
            # Executar transação de compra REAL via Solana
            logger.info("🚀 Executando compra REAL na blockchain...")
            buy_result = self.trader.buy_token(token_address, max_amount_sol)
            
            if not buy_result:
                logger.error("❌ Falha na execução da transação")
                return None
            
            # Extrair dados do resultado
            if isinstance(buy_result, dict):
                transaction_hash = buy_result.get('transaction_hash')
                token_amount = buy_result.get('tokens_bought', 0)
                logger.info(f"✅ Compra executada! Hash: {transaction_hash}")
                logger.info(f"✅ Tokens calculados: {token_amount:,.6f}")
                
                # VALIDAÇÃO CRÍTICA: Verificar saldo REAL após compra
                logger.info("🔍 Verificando saldo real na carteira...")
                import time
                time.sleep(5)  # Aguardar confirmação na blockchain
                
                real_balance = self.trader.get_token_balance(token_address)
                if real_balance > 0:
                    logger.info(f"📊 Saldo real na carteira: {real_balance:,.6f} tokens")
                    
                    # Se houver grande discrepância, usar o saldo real
                    if abs(real_balance - token_amount) / token_amount > 0.1:  # Mais de 10% de diferença
                        logger.warning(f"⚠️ DISCREPÂNCIA DETECTADA!")
                        logger.warning(f"   Calculado: {token_amount:,.6f}")
                        logger.warning(f"   Real: {real_balance:,.6f}")
                        logger.warning(f"   🔄 USANDO SALDO REAL!")
                        token_amount = real_balance
                        
            else:
                # Compatibilidade com retorno antigo (apenas string)
                transaction_hash = buy_result
                sol_price_usd = self._get_sol_price()  
                amount_usd = max_amount_sol * sol_price_usd
                token_amount = amount_usd / current_price if current_price > 0 else 0
                logger.info(f"✅ Compra executada! Hash: {transaction_hash}")
            
            # Registrar no banco
            trade_id = self._record_buy_transaction(
                token_data=token_data,
                buy_price=current_price,
                buy_amount=token_amount,
                transaction_hash=transaction_hash,
                sol_amount=max_amount_sol,
                suggestion_id=suggestion_id  # Usar parâmetro suggestion_id em vez do token_data
            )
            
            if trade_id:
                logger.info(f"✅ Compra registrada com sucesso! Trade ID: {trade_id}")
                
                # Enviar notificação com preço real
                token_data_with_real_price = token_data.copy()
                token_data_with_real_price['price_usd'] = current_price
                self._send_buy_notification(token_data_with_real_price, trade_id, token_amount, max_amount_sol)
                
                return {
                    'trade_id': trade_id,
                    'token_address': token_address,
                    'symbol': token_data.get('symbol'),
                    'buy_price': current_price,
                    'buy_amount': token_amount,
                    'sol_amount': max_amount_sol,
                    'transaction_hash': transaction_hash
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Erro ao executar compra: {e}")
            return None
    
    def _record_buy_transaction(self, token_data: Dict, buy_price: float, 
                                buy_amount: float, transaction_hash: str, sol_amount: float = 0.05, 
                                suggestion_id: str = None) -> Optional[int]:
        """Registra a transação de compra no banco"""
        try:
            with self.db.get_cursor() as cursor:
                # CRÍTICO: Obter decimais do token para salvar no banco
                from trade.utils.solana_client import SolanaTrader
                trader = SolanaTrader()
                token_decimals = trader._get_token_decimals(token_data.get('token_address'))
                
                cursor.execute("""
                    INSERT INTO trades (
                        token_address, token_name, token_symbol,
                        buy_price, buy_amount, buy_transaction_hash,
                        status, suggestion_id, token_decimals
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, 'OPEN', %s, %s
                    ) RETURNING id
                """, (
                    token_data.get('token_address'),
                    token_data.get('token_name', token_data.get('symbol', 'Unknown')),  # Tenta token_name primeiro, depois symbol
                    token_data.get('token_symbol', token_data.get('symbol', 'Unknown')),  # Tenta token_symbol primeiro, depois symbol
                    buy_price,
                    buy_amount,
                    transaction_hash,
                    suggestion_id or token_data.get('suggestion_id'),  # Priorizar parâmetro suggestion_id
                    token_decimals
                ))
                
                result = cursor.fetchone()
                return result['id'] if result else None
                
        except Exception as e:
            logger.error(f"Erro ao registrar compra: {e}")
            return None
    
    
    def _get_sol_price(self) -> float:
        """
        Busca o preço atual de SOL em USD
        TODO: Implementar busca real via API
        """
        # Por enquanto usar valor fixo para testes
        return 150.0
    
    def _get_current_token_price(self, token_address: str) -> Optional[float]:
        """
        Busca o preço atual do token usando DEXTools API
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
    
    def _send_buy_notification(self, token_data: Dict, trade_id: int, 
                               amount: float, sol_amount: float):
        """Envia notificação de compra via Telegram"""
        try:
            from backend.services.telegram_notifier import telegram_notifier
            
            message = f"""💰 <b>NOVA COMPRA EXECUTADA!</b>

🪙 Token: <b>{token_data.get('symbol')}</b>
📝 Nome: {token_data.get('token_name', 'Unknown')}
💵 Preço: ${token_data.get('price_usd', 0):.8f}
📊 Quantidade: {amount:.4f} tokens
💸 Investido: {sol_amount} SOL

🎯 Target: +{self.config.get('profit_target_percentage', '20')}% (venda automática)
🛑 Stop Loss: -{self.config.get('stop_loss_percentage', '10')}% (venda automática)

🆔 Trade ID: #{trade_id}
📍 Token: <code>{token_data.get('token_address')}</code>

🤖 Sistema de Trading Automático v1.0"""
            
            telegram_notifier.send_notification(message, "TRADE_BUY")
            
        except Exception as e:
            logger.error(f"Erro ao enviar notificação: {e}")

# Instância global
buy_service = BuyService()