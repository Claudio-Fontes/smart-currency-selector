#!/usr/bin/env python3
"""
Script COMPLETO de sincronização com integração Solscan
- Busca histórico de transações via Solscan
- Importa tokens da carteira com valor > $1
- Obtém preço médio de compra real das transações
"""

import logging
import sys
import json
import requests
from pathlib import Path
from decimal import Decimal, getcontext
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
import time

sys.path.insert(0, str(Path(__file__).parent))

from trade.utils.solana_client import SolanaTrader
from backend.services.dextools_service import DEXToolsService

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SolscanIntegration:
    def __init__(self, wallet_address):
        self.wallet_address = wallet_address
        self.base_url = "https://api.solscan.io"
        self.headers = {
            'accept': 'application/json',
            'User-Agent': 'Mozilla/5.0'
        }

    def get_token_transactions(self, token_address):
        """Busca transações de um token específico via Solscan"""
        try:
            # URL para buscar transferências do token
            url = f"{self.base_url}/v2/account/transactions"
            params = {
                'address': self.wallet_address,
                'type': 'TOKEN_TRANSFER',
                'token': token_address,
                'limit': 50
            }

            response = requests.get(url, params=params, headers=self.headers)

            if response.status_code == 200:
                data = response.json()
                return data.get('data', [])
            else:
                logger.warning(f"Solscan API retornou status {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"Erro ao buscar transações via Solscan: {e}")
            return []

    def get_token_balance_and_history(self, token_address):
        """Busca saldo e histórico de um token"""
        try:
            # Buscar informações do token holder
            url = f"{self.base_url}/v2/token/holder"
            params = {
                'token': token_address,
                'address': self.wallet_address
            }

            response = requests.get(url, params=params, headers=self.headers)

            if response.status_code == 200:
                return response.json()
            else:
                return None

        except Exception as e:
            logger.error(f"Erro ao buscar dados do token: {e}")
            return None

    def get_average_buy_price(self, token_address):
        """Calcula preço médio de compra baseado no histórico"""
        try:
            transactions = self.get_token_transactions(token_address)

            if not transactions:
                return None

            total_spent = Decimal('0')
            total_tokens = Decimal('0')

            for tx in transactions:
                # Analisar apenas transações de compra (incoming)
                if tx.get('type') == 'TOKEN_TRANSFER' and tx.get('direction') == 'in':
                    amount = Decimal(str(tx.get('amount', 0)))
                    price = Decimal(str(tx.get('price', 0)))

                    if amount > 0 and price > 0:
                        total_spent += amount * price
                        total_tokens += amount

            if total_tokens > 0:
                avg_price = total_spent / total_tokens
                return float(avg_price)

            return None

        except Exception as e:
            logger.error(f"Erro ao calcular preço médio: {e}")
            return None

class AdvancedWalletSync:
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
        self.wallet_address = self.trader.wallet_address
        self.solscan = SolscanIntegration(self.wallet_address)
        getcontext().prec = 18
        self.min_value_usd = 1.0

    def get_wallet_tokens_with_history(self):
        """Busca tokens na carteira com histórico de transações"""
        logger.info("🔍 Buscando tokens na carteira com histórico via Solscan...")
        logger.info(f"📍 Carteira: {self.wallet_address}")

        try:
            # Primeiro, buscar todos os tokens via RPC
            from solana.rpc.api import Client
            from solana.rpc.types import TokenAccountOpts
            from spl.token.constants import TOKEN_PROGRAM_ID
            from solders.pubkey import Pubkey

            client = Client(self.trader.rpc_endpoint)
            wallet_pubkey = Pubkey.from_string(self.wallet_address)

            opts = TokenAccountOpts(program_id=TOKEN_PROGRAM_ID)
            response = client.get_token_accounts_by_owner(wallet_pubkey, opts)

            tokens_with_value = []

            if response.value:
                logger.info(f"📊 Encontradas {len(response.value)} contas de token")

                for account in response.value:
                    try:
                        # Obter informações básicas do token
                        account_info = client.get_account_info(account.pubkey)

                        if account_info and account_info.value:
                            from spl.token.instructions import decode_account_data
                            account_data = decode_account_data(account_info.value.data)

                            mint_address = str(account_data.mint)
                            balance = account_data.amount / (10 ** account_data.decimals)

                            if balance > 0:
                                # Buscar preço atual via DEXTools
                                price_info = self.dextools.get_token_price(mint_address)
                                current_price = 0

                                if price_info and price_info.get('success'):
                                    current_price = float(price_info.get('data', {}).get('price', 0))

                                value_usd = balance * current_price

                                if value_usd >= self.min_value_usd:
                                    # Buscar informações do token
                                    token_info = self.dextools.get_token_info(mint_address)
                                    symbol = 'UNKNOWN'
                                    name = 'Unknown Token'

                                    if token_info and token_info.get('success'):
                                        data = token_info.get('data', {})
                                        symbol = data.get('symbol', 'UNKNOWN')
                                        name = data.get('name', 'Unknown Token')

                                    # Buscar preço médio de compra via Solscan
                                    logger.info(f"\n  🔍 Buscando histórico para {symbol}...")
                                    avg_buy_price = self.solscan.get_average_buy_price(mint_address)

                                    if not avg_buy_price:
                                        # Se não conseguir via Solscan, usar preço atual
                                        avg_buy_price = current_price
                                        logger.info(f"    ⚠️ Usando preço atual como referência")
                                    else:
                                        logger.info(f"    ✅ Preço médio de compra: ${avg_buy_price:.8f}")

                                    token_data = {
                                        'mint_address': mint_address,
                                        'symbol': symbol,
                                        'name': name,
                                        'balance': balance,
                                        'current_price': current_price,
                                        'avg_buy_price': avg_buy_price,
                                        'value_usd': value_usd
                                    }

                                    tokens_with_value.append(token_data)

                                    # Calcular PnL
                                    if avg_buy_price > 0:
                                        pnl = ((current_price - avg_buy_price) / avg_buy_price) * 100
                                        logger.info(f"  💰 {symbol}: {balance:.2f} tokens")
                                        logger.info(f"     Valor: ${value_usd:.2f}")
                                        logger.info(f"     PnL: {pnl:+.2f}%")

                    except Exception as e:
                        logger.debug(f"  ⚠️ Erro ao processar token: {e}")
                        continue

                # Aguardar um pouco para não sobrecarregar APIs
                time.sleep(0.5)

            logger.info(f"\n💰 Total de tokens com valor >= ${self.min_value_usd}: {len(tokens_with_value)}")
            return tokens_with_value

        except Exception as e:
            logger.error(f"❌ Erro ao buscar tokens: {e}")
            return []

    def create_position_with_history(self, token_data):
        """Cria posição com preço médio real de compra"""
        try:
            cur = self.conn.cursor()

            # Usar preço médio de compra se disponível
            buy_price = token_data.get('avg_buy_price', token_data['current_price'])

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
                str(buy_price),
                str(token_data['balance']),
                'SOLSCAN_IMPORT',
                datetime.now(),
                'OPEN'
            ))

            trade_id = cur.fetchone()[0]
            self.conn.commit()

            # Calcular PnL
            pnl = 0
            if buy_price > 0:
                pnl = ((token_data['current_price'] - buy_price) / buy_price) * 100

            logger.info(f"✅ Criada posição ID {trade_id} para {token_data['symbol']}")
            logger.info(f"   Preço médio: ${buy_price:.8f}")
            logger.info(f"   PnL atual: {pnl:+.2f}%")

            return trade_id

        except Exception as e:
            self.conn.rollback()
            logger.error(f"❌ Erro ao criar posição: {e}")
            return None

    def sync_positions(self):
        """Sincroniza posições com dados completos"""
        logger.info("="*80)
        logger.info("🔄 SINCRONIZAÇÃO COMPLETA COM SOLSCAN")
        logger.info("="*80)
        logger.info(f"💰 Valor mínimo: ${self.min_value_usd:.2f}")
        logger.info(f"📍 Carteira: {self.wallet_address}")

        # 1. Buscar tokens com histórico
        wallet_tokens = self.get_wallet_tokens_with_history()
        wallet_tokens_dict = {t['mint_address']: t for t in wallet_tokens}

        # 2. Buscar posições no banco
        cur = self.conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT id, token_address, token_symbol, buy_amount
            FROM trades
            WHERE status = 'OPEN'
        """)
        db_positions = cur.fetchall()
        db_tokens_set = {p['token_address'] for p in db_positions}

        # 3. Identificar tokens novos
        new_tokens = []
        for mint_address, token_data in wallet_tokens_dict.items():
            if mint_address not in db_tokens_set:
                new_tokens.append(token_data)

        # 4. Importar tokens novos
        if new_tokens:
            logger.info(f"\n🆕 TOKENS NOVOS PARA IMPORTAR:")
            logger.info("-"*60)

            for token in new_tokens:
                logger.info(f"\n📌 {token['symbol']} ({token['mint_address'][:20]}...)")
                logger.info(f"   Balance: {token['balance']:.2f} tokens")
                logger.info(f"   Valor: ${token['value_usd']:.2f}")

                if self.create_position_with_history(token):
                    logger.info(f"   ✅ Importado com sucesso!")
                else:
                    logger.info(f"   ❌ Falha ao importar")

                time.sleep(1)  # Delay entre importações

        # 5. Verificar posições existentes
        logger.info(f"\n📊 VERIFICANDO POSIÇÕES EXISTENTES:")
        logger.info("-"*60)

        maintained = 0
        closed = 0

        for position in db_positions:
            if position['token_address'] in wallet_tokens_dict:
                wallet_data = wallet_tokens_dict[position['token_address']]
                logger.info(f"✅ {position['token_symbol']}: Mantido (${wallet_data['value_usd']:.2f})")
                maintained += 1
            else:
                logger.info(f"⚠️ {position['token_symbol']}: Fechando (não encontrado ou < ${self.min_value_usd})")
                self.close_position(position['id'])
                closed += 1

        # 6. Resumo
        logger.info(f"\n{'='*80}")
        logger.info(f"📈 RESULTADO:")
        logger.info(f"   🆕 Importados: {len(new_tokens)}")
        logger.info(f"   ✅ Mantidos: {maintained}")
        logger.info(f"   🔄 Fechados: {closed}")
        logger.info(f"{'='*80}")

        return {
            'imported': len(new_tokens),
            'maintained': maintained,
            'closed': closed
        }

    def close_position(self, position_id):
        """Fecha posição"""
        try:
            cur = self.conn.cursor()
            cur.execute("""
                UPDATE trades SET
                    status = 'CLOSED',
                    sell_time = NOW(),
                    sell_reason = 'SYNC_NOT_IN_WALLET',
                    updated_at = NOW()
                WHERE id = %s
            """, (position_id,))
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Erro ao fechar posição: {e}")
            return False

def main():
    """Função principal"""
    logger.info("🚀 Iniciando sincronização com Solscan")

    try:
        sync = AdvancedWalletSync()
        result = sync.sync_positions()

        logger.info("\n✅ Sincronização concluída!")
        return result

    except Exception as e:
        logger.error(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    main()