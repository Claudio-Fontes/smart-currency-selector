#!/usr/bin/env python3
"""
Script SIMPLES de sincronização usando Solana CLI
Importa tokens não rastreados com valor > $1
"""

import subprocess
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from backend.services.dextools_service import DEXToolsService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimpleWalletSync:
    def __init__(self):
        self.wallet_address = "5cQfESQeA1XZQT6C6JA3E9J9Vg7jp1KT4ttj8Pmw5V4R"
        self.conn = psycopg2.connect(
            host='localhost',
            port=5432,
            user='lucia',
            password='lucia',
            database='cm_bot'
        )
        self.dextools = DEXToolsService()
        self.min_value_usd = 1.0

    def get_wallet_tokens_cli(self):
        """Usa solana CLI para obter tokens"""
        logger.info("🔍 Buscando tokens na carteira via CLI...")

        try:
            # Tentar usar spl-token para listar tokens
            result = subprocess.run(
                ['spl-token', 'accounts', '--owner', self.wallet_address, '--output', 'json'],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                tokens = json.loads(result.stdout)
                return self.process_tokens(tokens)
            else:
                logger.error(f"Erro ao executar spl-token: {result.stderr}")
                return []

        except FileNotFoundError:
            logger.warning("spl-token não encontrado, tentando método alternativo...")
            return self.get_wallet_tokens_alternative()
        except Exception as e:
            logger.error(f"Erro: {e}")
            return []

    def get_wallet_tokens_alternative(self):
        """Método alternativo: buscar tokens conhecidos diretamente"""
        logger.info("📋 Usando método alternativo: verificando tokens conhecidos...")

        # Lista de tokens conhecidos que podem estar na carteira
        known_tokens = [
            # Adicione aqui os endereços dos tokens que você sabe que tem
            "ANTzKCA6jDqT3Vo35H5XroGqG1dyRfP3YAi2kuJVqANT",
            "CQDfbCK17ExoXA66nLS2XFrtwPVDhQJDdFRWErjx3Zba"
            # Adicione outros tokens aqui
        ]

        tokens_with_value = []

        for token_address in known_tokens:
            try:
                # Verificar se tem saldo deste token
                from trade.utils.solana_client import SolanaTrader
                import time

                trader = SolanaTrader()

                # Adicionar delay entre consultas para evitar rate limit
                time.sleep(1)
                balance = trader.get_token_balance(token_address)

                if balance > 0:
                    # Buscar preço
                    price_info = self.dextools.get_token_price(token_address)
                    if price_info and price_info.get('success'):
                        price = float(price_info.get('data', {}).get('price', 0))
                        value_usd = balance * price

                        if value_usd >= self.min_value_usd:
                            # Buscar informações do token
                            token_info = self.dextools.get_token_info(token_address)
                            symbol = 'UNKNOWN'
                            name = 'Unknown Token'

                            if token_info and token_info.get('success'):
                                data = token_info.get('data', {})
                                symbol = data.get('symbol', 'UNKNOWN')
                                name = data.get('name', 'Unknown Token')

                            tokens_with_value.append({
                                'mint_address': token_address,
                                'symbol': symbol,
                                'name': name,
                                'balance': balance,
                                'price': price,
                                'value_usd': value_usd
                            })

                            logger.info(f"  ✅ {symbol}: {balance:.2f} tokens (${value_usd:.2f})")

            except Exception as e:
                logger.warning(f"  ⚠️ Erro ao verificar {token_address}: {e}")
                continue

        return tokens_with_value

    def process_tokens(self, raw_tokens):
        """Processa tokens e filtra por valor"""
        tokens_with_value = []

        for token in raw_tokens:
            try:
                mint_address = token.get('mint', '')
                balance = float(token.get('amount', 0))

                if balance > 0:
                    # Buscar preço
                    price_info = self.dextools.get_token_price(mint_address)
                    if price_info and price_info.get('success'):
                        price = float(price_info.get('data', {}).get('price', 0))
                        value_usd = balance * price

                        if value_usd >= self.min_value_usd:
                            # Buscar informações do token
                            token_info = self.dextools.get_token_info(mint_address)
                            symbol = token.get('symbol', 'UNKNOWN')
                            name = token.get('name', 'Unknown Token')

                            if token_info and token_info.get('success'):
                                data = token_info.get('data', {})
                                symbol = data.get('symbol', symbol)
                                name = data.get('name', name)

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
                logger.debug(f"  Erro ao processar token: {e}")
                continue

        return tokens_with_value

    def sync_positions(self):
        """Sincroniza posições"""
        logger.info("="*60)
        logger.info("🔄 SINCRONIZAÇÃO SIMPLIFICADA")
        logger.info("="*60)
        logger.info(f"💰 Valor mínimo: ${self.min_value_usd:.2f}")
        logger.info(f"📍 Carteira: {self.wallet_address}")

        # 1. Buscar tokens na carteira
        wallet_tokens = self.get_wallet_tokens_alternative()  # Usar método alternativo

        if not wallet_tokens:
            logger.info("❌ Nenhum token com valor > $1 encontrado")
            return {'imported': 0, 'maintained': 0, 'closed': 0}

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
        imported = 0
        if new_tokens:
            logger.info(f"\n🆕 TOKENS PARA IMPORTAR:")
            logger.info("-"*50)

            for token in new_tokens:
                logger.info(f"\n📌 {token['symbol']} ({token['mint_address'][:20]}...)")
                logger.info(f"   Balance: {token['balance']:.2f} tokens")
                logger.info(f"   Valor: ${token['value_usd']:.2f}")

                try:
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
                        token['mint_address'],
                        token['symbol'],
                        token['name'],
                        str(token['price']),
                        str(token['balance']),
                        'WALLET_IMPORT',
                        datetime.now(),
                        'OPEN'
                    ))

                    trade_id = cur.fetchone()['id']
                    self.conn.commit()

                    logger.info(f"   ✅ Importado com ID {trade_id}")
                    imported += 1

                except Exception as e:
                    self.conn.rollback()
                    logger.error(f"   ❌ Erro ao importar: {e}")

        # 5. Verificar posições existentes
        maintained = 0
        closed = 0

        logger.info(f"\n📊 VERIFICANDO POSIÇÕES EXISTENTES:")
        logger.info("-"*50)

        for position in db_positions:
            if position['token_address'] in wallet_tokens_dict:
                wallet_data = wallet_tokens_dict[position['token_address']]
                logger.info(f"✅ {position['token_symbol']}: Mantido (${wallet_data['value_usd']:.2f})")
                maintained += 1
            else:
                logger.info(f"⚠️ {position['token_symbol']}: Fechando (não encontrado ou < ${self.min_value_usd})")

                try:
                    cur.execute("""
                        UPDATE trades SET
                            status = 'CLOSED',
                            sell_time = NOW(),
                            sell_reason = 'SYNC_NOT_IN_WALLET',
                            updated_at = NOW()
                        WHERE id = %s
                    """, (position['id'],))
                    self.conn.commit()
                    closed += 1
                except Exception as e:
                    self.conn.rollback()
                    logger.error(f"   Erro ao fechar: {e}")

        # 6. Resumo
        logger.info(f"\n{'='*60}")
        logger.info(f"📈 RESULTADO:")
        logger.info(f"   🆕 Importados: {imported}")
        logger.info(f"   ✅ Mantidos: {maintained}")
        logger.info(f"   🔄 Fechados: {closed}")
        logger.info(f"{'='*60}")

        return {
            'imported': imported,
            'maintained': maintained,
            'closed': closed
        }

def main():
    """Função principal"""
    logger.info("🚀 Iniciando sincronização simplificada")

    try:
        sync = SimpleWalletSync()
        result = sync.sync_positions()

        logger.info("\n✅ Sincronização concluída!")

        # Perguntar se deseja adicionar tokens manualmente
        logger.info("\n💡 Para adicionar tokens específicos que não foram detectados:")
        logger.info("   Execute: python3 add_token_manual.py <TOKEN_ADDRESS>")

        return result

    except Exception as e:
        logger.error(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    main()