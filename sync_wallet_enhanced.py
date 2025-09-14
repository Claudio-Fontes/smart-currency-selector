#!/usr/bin/env python3
"""
Script MELHORADO de sincronização entre carteira real e posições no banco
- Importa tokens da carteira com valor > $1 que não estão na base
- Fecha posições onde o saldo real é menor que $1.00
- Cria novas posições para tokens não rastreados
"""

import logging
import sys
from pathlib import Path
from decimal import Decimal, getcontext
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor

sys.path.insert(0, str(Path(__file__).parent))

from trade.utils.solana_client import SolanaTrader
from backend.services.dextools_service import DEXToolsService

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EnhancedWalletSync:
    def __init__(self):
        self.conn = psycopg2.connect(
            host='localhost',
            port=5432,
            user='lucia',
            password='lucia',
            database='cm_bot'
        )
        self.trader = SolanaTrader()
        self.dextools = DEXToolsService()
        getcontext().prec = 18
        self.min_value_usd = 1.0

    def get_all_wallet_tokens(self):
        """Busca todos os tokens na carteira com valor > $1"""
        logger.info("🔍 Buscando todos os tokens na carteira...")

        try:
            # Usar o método do SolanaTrader para obter balances
            wallet_address = self.trader.wallet.pubkey()
            logger.info(f"📍 Carteira: {wallet_address}")

            # Obter todas as contas de token
            from solana.rpc.types import TokenAccountOpts
            from solders.pubkey import Pubkey
            from spl.token.constants import TOKEN_PROGRAM_ID

            opts = TokenAccountOpts(program_id=TOKEN_PROGRAM_ID)
            response = self.trader.client.get_token_accounts_by_owner(wallet_address, opts)

            tokens_with_value = []

            if response.value:
                logger.info(f"📊 Encontradas {len(response.value)} contas de token")

                for account in response.value:
                    try:
                        # Obter informações do token
                        token_address = str(account.pubkey)
                        account_info = self.trader.client.get_account_info(account.pubkey)

                        if account_info and account_info.value:
                            # Decodificar dados da conta
                            from spl.token.instructions import decode_account_data
                            account_data = decode_account_data(account_info.value.data)

                            mint_address = str(account_data.mint)
                            balance = account_data.amount / (10 ** account_data.decimals)

                            if balance > 0:
                                # Buscar preço atual
                                price_info = self.dextools.get_token_price(mint_address)
                                if price_info and price_info.get('success'):
                                    price = float(price_info.get('data', {}).get('price', 0))
                                    value_usd = balance * price

                                    if value_usd >= self.min_value_usd:
                                        # Buscar informações adicionais do token
                                        token_info = self.dextools.get_token_info(mint_address)
                                        symbol = 'UNKNOWN'
                                        name = 'Unknown Token'

                                        if token_info and token_info.get('success'):
                                            data = token_info.get('data', {})
                                            symbol = data.get('symbol', 'UNKNOWN')
                                            name = data.get('name', 'Unknown Token')

                                        tokens_with_value.append({
                                            'mint_address': mint_address,
                                            'symbol': symbol,
                                            'name': name,
                                            'balance': balance,
                                            'price': price,
                                            'value_usd': value_usd
                                        })

                                        logger.info(f"  ✅ {symbol}: {balance:.2f} tokens (${value_usd:.2f})")

                    except Exception as e:
                        logger.debug(f"  ⚠️ Erro ao processar conta {account.pubkey}: {e}")
                        continue

            logger.info(f"💰 Total de tokens com valor >= ${self.min_value_usd}: {len(tokens_with_value)}")
            return tokens_with_value

        except Exception as e:
            logger.error(f"❌ Erro ao buscar tokens da carteira: {e}")
            return []

    def get_open_positions(self):
        """Busca todas as posições abertas no banco"""
        try:
            cur = self.conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("""
                SELECT id, token_address, token_symbol, token_name,
                       buy_price, buy_amount, buy_time
                FROM trades
                WHERE status = 'OPEN'
                ORDER BY buy_time DESC
            """)

            positions = cur.fetchall()
            logger.info(f"📊 Encontradas {len(positions)} posições OPEN no banco")
            return positions

        except Exception as e:
            logger.error(f"❌ Erro ao buscar posições: {e}")
            return []

    def create_position_from_wallet(self, token_data):
        """Cria nova posição para token encontrado na carteira"""
        try:
            cur = self.conn.cursor()

            # Inserir nova trade como posição aberta
            cur.execute("""
                INSERT INTO trades (
                    token_address, token_symbol, token_name,
                    buy_price, buy_amount, buy_transaction_hash,
                    buy_time, status, created_at, updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()
                )
                RETURNING id
            """, (
                token_data['mint_address'],
                token_data['symbol'],
                token_data['name'],
                str(token_data['price']),
                str(token_data['balance']),
                'WALLET_IMPORT',  # Hash especial para indicar importação
                datetime.now(),
                'OPEN'
            ))

            trade_id = cur.fetchone()[0]
            self.conn.commit()

            logger.info(f"✅ Criada posição ID {trade_id} para {token_data['symbol']}")
            return trade_id

        except Exception as e:
            self.conn.rollback()
            logger.error(f"❌ Erro ao criar posição: {e}")
            return None

    def sync_positions(self):
        """Sincroniza posições com carteira real"""
        logger.info("="*60)
        logger.info("🔄 SINCRONIZAÇÃO AVANÇADA CARTEIRA <-> BANCO")
        logger.info("="*60)
        logger.info(f"💰 Valor mínimo para rastrear: ${self.min_value_usd:.2f}")

        # 1. Buscar todos os tokens na carteira
        wallet_tokens = self.get_all_wallet_tokens()
        wallet_tokens_dict = {t['mint_address']: t for t in wallet_tokens}

        # 2. Buscar posições abertas no banco
        db_positions = self.get_open_positions()
        db_tokens_set = {p['token_address'] for p in db_positions}

        # 3. Identificar tokens novos (na carteira mas não no banco)
        new_tokens = []
        for mint_address, token_data in wallet_tokens_dict.items():
            if mint_address not in db_tokens_set:
                new_tokens.append(token_data)

        # 4. Processar tokens novos
        if new_tokens:
            logger.info(f"\n🆕 TOKENS NOVOS ENCONTRADOS NA CARTEIRA:")
            logger.info("-"*50)

            for token in new_tokens:
                logger.info(f"\n📌 {token['symbol']} ({token['mint_address'][:20]}...)")
                logger.info(f"   Balance: {token['balance']:.2f} tokens")
                logger.info(f"   Preço: ${token['price']:.8f}")
                logger.info(f"   Valor: ${token['value_usd']:.2f}")

                # Criar posição no banco
                if self.create_position_from_wallet(token):
                    logger.info(f"   ✅ Importado para o banco com sucesso!")
                else:
                    logger.info(f"   ❌ Falha ao importar")
        else:
            logger.info("\n✅ Nenhum token novo encontrado na carteira")

        # 5. Verificar posições existentes
        logger.info(f"\n📊 VERIFICANDO POSIÇÕES EXISTENTES:")
        logger.info("-"*50)

        closed_positions = 0
        maintained_positions = 0

        for position in db_positions:
            token_address = position['token_address']

            if token_address in wallet_tokens_dict:
                # Token ainda está na carteira
                wallet_data = wallet_tokens_dict[token_address]
                logger.info(f"\n✅ {position['token_symbol']}: Mantido")
                logger.info(f"   DB: {position['buy_amount']:.2f} tokens")
                logger.info(f"   Wallet: {wallet_data['balance']:.2f} tokens")
                logger.info(f"   Valor atual: ${wallet_data['value_usd']:.2f}")
                maintained_positions += 1
            else:
                # Token não está mais na carteira ou valor < $1
                logger.info(f"\n⚠️ {position['token_symbol']}: Não encontrado ou valor < ${self.min_value_usd}")

                # Verificar saldo real
                try:
                    balance = self.trader.get_token_balance(token_address)
                    if balance > 0:
                        price_info = self.dextools.get_token_price(token_address)
                        if price_info and price_info.get('success'):
                            price = float(price_info.get('data', {}).get('price', 0))
                            value_usd = balance * price

                            if value_usd < self.min_value_usd:
                                logger.info(f"   Saldo: {balance:.2f} tokens (${value_usd:.2f}) - Fechando posição")
                                self.close_position(position['id'], 'LOW_VALUE')
                                closed_positions += 1
                            else:
                                logger.info(f"   Mantendo - valor ${value_usd:.2f}")
                                maintained_positions += 1
                    else:
                        logger.info(f"   Saldo ZERO - Fechando posição")
                        self.close_position(position['id'], 'ZERO_BALANCE')
                        closed_positions += 1
                except Exception as e:
                    logger.error(f"   Erro ao verificar: {e}")

        # 6. Resumo final
        logger.info(f"\n{'='*60}")
        logger.info(f"📈 RESULTADO DA SINCRONIZAÇÃO:")
        logger.info(f"   🆕 Tokens importados: {len(new_tokens)}")
        logger.info(f"   ✅ Posições mantidas: {maintained_positions}")
        logger.info(f"   🔄 Posições fechadas: {closed_positions}")
        logger.info(f"   📊 Total de tokens rastreados: {maintained_positions + len(new_tokens)}")
        logger.info(f"{'='*60}")

        return {
            'imported': len(new_tokens),
            'maintained': maintained_positions,
            'closed': closed_positions
        }

    def close_position(self, position_id, reason):
        """Fecha posição no banco"""
        try:
            cur = self.conn.cursor()
            cur.execute("""
                UPDATE trades SET
                    sell_price = 0,
                    sell_amount = 0,
                    sell_transaction_hash = %s,
                    sell_time = NOW(),
                    sell_reason = %s,
                    profit_loss_amount = 0,
                    profit_loss_percentage = 0,
                    status = 'CLOSED',
                    updated_at = NOW()
                WHERE id = %s
            """, (f'SYNC_{reason}', reason, position_id))

            self.conn.commit()
            return True

        except Exception as e:
            self.conn.rollback()
            logger.error(f"❌ Erro ao fechar posição {position_id}: {e}")
            return False

def main():
    """Função principal"""
    logger.info("🚀 Iniciando sincronização avançada de carteira")

    try:
        sync = EnhancedWalletSync()
        result = sync.sync_positions()

        logger.info("\n✅ Sincronização concluída com sucesso!")
        return result

    except Exception as e:
        logger.error(f"❌ Erro na sincronização: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    main()