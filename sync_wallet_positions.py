#!/usr/bin/env python3
"""
Script de sincronização entre carteira real e posições no banco
Fecha posições onde o saldo real é menor que $1.00
"""

import logging
import sys
from pathlib import Path
from decimal import Decimal, getcontext
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from trade.database.connection import TradeDatabase
from trade.utils.solana_client import SolanaTrader
from backend.services.dextools_service import DEXToolsService

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WalletSync:
    def __init__(self):
        self.db = TradeDatabase()
        self.trader = SolanaTrader()
        self.dextools = DEXToolsService()
        getcontext().prec = 18
    
    def get_open_positions(self):
        """Busca todas as posições abertas no banco"""
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute("""
                    SELECT id, token_address, token_symbol, token_name, 
                           buy_price, buy_amount, buy_time
                    FROM trades 
                    WHERE status = 'OPEN'
                    ORDER BY buy_time DESC
                """)
                
                positions = cursor.fetchall()
                logger.info(f"📊 Encontradas {len(positions)} posições OPEN no banco")
                return positions
                
        except Exception as e:
            logger.error(f"❌ Erro ao buscar posições: {e}")
            return []
    
    def get_real_wallet_balance(self, token_address):
        """Consulta saldo real na carteira"""
        try:
            balance = self.trader.get_token_balance(token_address)
            logger.debug(f"   Saldo na carteira: {balance:.10f}")
            return balance

        except Exception as e:
            # Log limpo - sem spam de erros
            logger.debug(f"⚠️ Erro consulta saldo {token_address[:8]}: {str(e)[:30]}...")
            return 0.0
    
    def get_current_token_price(self, token_address):
        """Busca preço atual do token"""
        try:
            token_info = self.dextools.get_token_price(token_address)
            if token_info and token_info.get('success'):
                price = float(token_info.get('data', {}).get('price', 0))
                logger.debug(f"   Preço atual: ${price:.8f}")
                return price
            return 0.0
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar preço: {e}")
            return 0.0
    
    def close_position_as_manual_sync(self, position_id, token_address, real_balance, reason="MANUAL_SYNC"):
        """Fecha posição no banco como venda manual"""
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute("""
                    UPDATE trades SET
                        sell_price = 0,
                        sell_amount = %s,
                        sell_transaction_hash = 'MANUAL_SYNC',
                        sell_time = NOW(),
                        sell_reason = %s,
                        profit_loss_amount = 0,
                        profit_loss_percentage = 0,
                        status = 'CLOSED',
                        updated_at = NOW()
                    WHERE id = %s
                """, (real_balance, reason, position_id))
                
                logger.info(f"✅ Posição {position_id} fechada como {reason}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Erro ao fechar posição {position_id}: {e}")
            return False
    
    def sync_positions(self, min_value_usd=1.0):
        """Sincroniza posições com carteira real"""
        logger.info("🔄 Iniciando sincronização carteira <-> banco")
        logger.info(f"💰 Valor mínimo para manter posição: ${min_value_usd:.2f}")
        
        positions = self.get_open_positions()
        if not positions:
            logger.info("ℹ️ Nenhuma posição aberta encontrada")
            return
        
        synced_positions = 0
        closed_positions = 0
        
        for position in positions:
            logger.info(f"\n📊 Analisando posição ID {position['id']}: {position['token_symbol']}")
            logger.info(f"   Token: {position['token_address']}")
            logger.info(f"   Comprado em: {position['buy_time']}")
            logger.info(f"   Quantidade no banco: {position['buy_amount']:.10f}")
            
            # Consultar saldo real
            real_balance = self.get_real_wallet_balance(position['token_address'])
            
            if real_balance <= 0:
                logger.warning(f"⚠️ Saldo ZERO na carteira - posição vendida manualmente")
                if self.close_position_as_manual_sync(position['id'], position['token_address'], 0, "MANUAL_ZERO_BALANCE"):
                    closed_positions += 1
                continue
            
            # Calcular valor atual em USD
            current_price = self.get_current_token_price(position['token_address'])
            current_value_usd = real_balance * current_price if current_price > 0 else 0
            
            logger.info(f"   💰 Valor atual: ${current_value_usd:.2f}")
            
            if current_value_usd < min_value_usd:
                logger.warning(f"⚠️ Valor < ${min_value_usd:.2f} - considerando como vendida manualmente")
                if self.close_position_as_manual_sync(
                    position['id'], 
                    position['token_address'], 
                    real_balance, 
                    f"MANUAL_LOW_VALUE_{current_value_usd:.2f}USD"
                ):
                    closed_positions += 1
            else:
                logger.info(f"✅ Posição mantida - valor suficiente")
                synced_positions += 1
        
        logger.info(f"\n📈 RESULTADO DA SINCRONIZAÇÃO:")
        logger.info(f"   ✅ Posições mantidas: {synced_positions}")
        logger.info(f"   🔄 Posições fechadas: {closed_positions}")
        logger.info(f"   📊 Total processado: {len(positions)}")
        
        return {
            'total_positions': len(positions),
            'maintained': synced_positions,
            'closed': closed_positions
        }

def main():
    """Função principal"""
    logger.info("🚀 Iniciando sincronização de carteira")
    
    try:
        sync = WalletSync()
        result = sync.sync_positions(min_value_usd=1.0)
        
        logger.info("✅ Sincronização concluída com sucesso!")
        return result
        
    except Exception as e:
        logger.error(f"❌ Erro na sincronização: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        # Fechar conexões
        try:
            sync.db.close()
        except:
            pass

if __name__ == "__main__":
    main()