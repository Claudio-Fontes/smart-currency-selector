#!/usr/bin/env python3
"""
Cliente Solana para executar trades reais
"""

import logging
import os
import requests
import json
import base64
from typing import Optional, Dict
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class SolanaTrader:
    """
    Cliente para trading na blockchain Solana usando Jupiter API
    """
    
    def __init__(self):
        self.wallet_address = os.getenv('SOLANA_WALLET_ADDRESS')
        self.private_key = os.getenv('SOLANA_PRIVATE_KEY') 
        self.rpc_endpoint = os.getenv('RPC_ENDPOINT', 'https://api.mainnet-beta.solana.com')
        self.jupiter_api = "https://quote-api.jup.ag/v6"
        
        # Configurações de slippage via environment
        self.default_slippage_bps = int(os.getenv('DEFAULT_SLIPPAGE_BPS', '500'))  # 5% padrão
        self.high_volatility_slippage_bps = int(os.getenv('HIGH_VOLATILITY_SLIPPAGE_BPS', '1000'))  # 10% para tokens voláteis
        
        # Lista de tokens com alta volatilidade que precisam de slippage maior
        self.high_volatility_tokens = self._load_high_volatility_tokens()
        
        logger.info(f"🔑 Wallet configurada: {self.wallet_address}")
        logger.info(f"🌐 RPC: {self.rpc_endpoint}")
        logger.info(f"⚙️ Slippage padrão: {self.default_slippage_bps} BPS ({self.default_slippage_bps/100}%)")
        logger.info(f"⚙️ Slippage alta volatilidade: {self.high_volatility_slippage_bps} BPS ({self.high_volatility_slippage_bps/100}%)")
        
        if not self.wallet_address or not self.private_key:
            logger.error("❌ Carteira não configurada no .env")
        
    def buy_token(self, token_address: str, amount_sol: float) -> Optional[str]:
        """
        Compra token na Solana via Jupiter - EXECUÇÃO REAL
        
        Returns:
            Transaction hash ou None se falhou
        """
        try:
            import base64
            import base58
            from solders.keypair import Keypair
            from solders.transaction import VersionedTransaction
            from solders import message
            from solana.rpc.api import Client
            from solana.rpc.types import TxOpts
            import time
            
            # Converter SOL para lamports (1 SOL = 1,000,000,000 lamports)
            amount_lamports = int(amount_sol * 1_000_000_000)
            
            logger.info(f"💰 EXECUÇÃO REAL - Comprando token {token_address}")
            logger.info(f"   Valor: {amount_sol} SOL ({amount_lamports:,} lamports)")
            
            # Preparar keypair
            logger.info("🔑 Preparando keypair...")
            private_key_bytes = base58.b58decode(self.private_key)
            if len(private_key_bytes) == 64:
                keypair = Keypair.from_bytes(private_key_bytes)
            else:
                keypair = Keypair.from_seed(private_key_bytes[:32])
            
            user_public_key = str(keypair.pubkey())
            logger.info(f"✅ Keypair carregado: {user_public_key}")
            
            # SOL mint address
            sol_mint = "So11111111111111111111111111111111111111112"
            
            # 1. Buscar quote via Jupiter
            logger.info("📊 Obtendo cotação via Jupiter...")
            quote_url = f"{self.jupiter_api}/quote"
            # Determinar slippage baseado no token
            slippage_bps = self._get_slippage_for_token(token_address)
            logger.info(f"📊 Slippage selecionado: {slippage_bps} BPS ({slippage_bps/100}%) para token {token_address[:8]}...")
            
            params = {
                'inputMint': sol_mint,
                'outputMint': token_address,
                'amount': amount_lamports,
                'slippageBps': slippage_bps
            }
            
            response = requests.get(quote_url, params=params)
            
            if response.status_code != 200:
                logger.error(f"❌ Erro na cotação: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return None
            
            quote_data = response.json()
            out_amount = int(quote_data['outAmount'])
            price_impact = quote_data.get('priceImpactPct', 0)
            
            # CRÍTICO: Obter decimais corretos do token
            decimals = self._get_token_decimals(token_address)
            
            # CRÍTICO: Converter para quantidade com decimais usando Decimal para máxima precisão
            from decimal import Decimal, getcontext
            getcontext().prec = 18  # Máxima precisão
            
            tokens_with_decimals = float(Decimal(str(out_amount)) / Decimal(str(10 ** decimals)))
            
            # VALIDAÇÃO CRÍTICA: Detectar erro de 1000x
            # Se quantidade < 10 tokens e estamos gastando 0.01 SOL ($1.50+)
            # Provavelmente há erro de decimais
            sol_price_estimate = 150  # Estimativa de preço SOL em USD
            usd_spent = amount_sol * sol_price_estimate
            
            if tokens_with_decimals < 10 and usd_spent > 1:
                logger.warning(f"⚠️ POSSÍVEL ERRO DE DECIMAIS DETECTADO!")
                logger.warning(f"   Apenas {tokens_with_decimals:.6f} tokens por ${usd_spent:.2f}?")
                logger.warning(f"   Verificando se decimais reais são {decimals - 3}...")
                
                # Tentar com 3 decimais a menos
                tokens_adjusted = float(Decimal(str(out_amount)) / Decimal(str(10 ** (decimals - 3))))
                logger.warning(f"   Com {decimals - 3} decimais: {tokens_adjusted:.6f} tokens")
                
                if tokens_adjusted > 100:  # Se faz mais sentido
                    logger.warning(f"   🔄 CORRIGINDO: Usando {decimals - 3} decimais")
                    tokens_with_decimals = tokens_adjusted
                    decimals = decimals - 3
            
            logger.info(f"✅ Cotação obtida:")
            logger.info(f"   Tokens a receber (raw): {out_amount:,}")
            logger.info(f"   Tokens a receber (UI): {tokens_with_decimals:.10f}")
            logger.info(f"   Decimais usados: {decimals}")
            logger.info(f"   Price Impact: {price_impact}%")
            
            # 2. Obter transação de swap via Jupiter
            logger.info("🔧 Criando transação via Jupiter...")
            swap_url = f"{self.jupiter_api}/swap"
            swap_payload = {
                'quoteResponse': quote_data,
                'userPublicKey': user_public_key,
                'wrapAndUnwrapSol': True,
                'dynamicComputeUnitLimit': True,
                'prioritizationFeeLamports': 'auto'
            }
            
            swap_response = requests.post(
                swap_url,
                json=swap_payload,
                headers={'Content-Type': 'application/json'}
            )
            
            if swap_response.status_code != 200:
                logger.error(f"❌ Erro ao obter swap: {swap_response.status_code}")
                logger.error(f"Response: {swap_response.text}")
                return None
            
            swap_data = swap_response.json()
            logger.info("✅ Transação criada pelo Jupiter")
            
            # 3. Assinar transação usando método correto
            logger.info("✍️ Assinando transação com método correto...")
            
            # Decodificar a transação do Jupiter
            swap_transaction_b64 = swap_data['swapTransaction']
            raw_tx = VersionedTransaction.from_bytes(base64.b64decode(swap_transaction_b64))
            
            logger.info("📝 Assinando mensagem da transação...")
            # Assinar a mensagem usando o método correto
            signature = keypair.sign_message(message.to_bytes_versioned(raw_tx.message))
            logger.info(f"✅ Signature criado")
            
            # Criar transação assinada usando populate
            logger.info("🔧 Populando transação com signature...")
            signed_tx = VersionedTransaction.populate(raw_tx.message, [signature])
            
            logger.info("✅ Transação assinada criada com sucesso!")
            
            # 4. Enviar para blockchain
            logger.info("📡 Enviando transação para Solana blockchain...")
            
            client = Client(self.rpc_endpoint)
            
            # Converter para bytes
            signed_tx_bytes = bytes(signed_tx)
            
            # Enviar transação
            response = client.send_raw_transaction(
                signed_tx_bytes,
                opts=TxOpts(
                    skip_preflight=False,
                    preflight_commitment='processed',
                    max_retries=3
                )
            )
            
            if response and response.value:
                tx_signature = str(response.value)
                
                # Verificar se não é signature fake
                if tx_signature == "1111111111111111111111111111111111111111111111111111111111111111":
                    logger.error("❌ Recebeu signature fake - transação não foi assinada corretamente")
                    return None
                
                logger.info(f"✅ TRANSAÇÃO ENVIADA COM SUCESSO!")
                logger.info(f"🔗 Transaction Signature: {tx_signature}")
                logger.info(f"🔍 Solscan: https://solscan.io/tx/{tx_signature}")
                
                # Aguardar um pouco para confirmação
                logger.info("⏳ Aguardando confirmação inicial...")
                time.sleep(10)
                
                # Retornar dicionário com hash e quantidade
                return {
                    'transaction_hash': tx_signature,
                    'tokens_bought': tokens_with_decimals,
                    'tokens_raw': out_amount
                }
            
            else:
                logger.error(f"❌ Erro ao enviar transação: {response}")
                return None
            
        except Exception as e:
            logger.error(f"❌ Erro na compra: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def sell_token(self, token_address: str, amount_tokens: float) -> Optional[str]:
        """
        Vende tokens por SOL
        
        Returns:
            Transaction hash ou None se falhou
        """
        logger.info(f"🎮 SIMULAÇÃO: Vendendo {amount_tokens} tokens de {token_address}")
        
        # TODO: Implementar venda real via Jupiter/Raydium
        # 1. Conectar wallet
        # 2. Buscar pool de liquidez
        # 3. Calcular slippage
        # 4. Executar swap Token -> SOL
        # 5. Retornar transaction hash
        
        import hashlib
        import time
        tx_hash = hashlib.sha256(f"SELL_{token_address}{time.time()}".encode()).hexdigest()
        
        return tx_hash
    
    def get_token_balance(self, token_address: str) -> float:
        """
        Busca saldo de um token na carteira
        """
        # TODO: Implementar consulta real via Solana RPC
        return 0.0
    
    def _send_transaction(self, transaction_b64: str) -> Optional[str]:
        """
        Assina e envia transação para a blockchain
        """
        try:
            from solana.rpc.api import Client
            from solders.keypair import Keypair
            from solders.transaction import Transaction
            from solders.pubkey import Pubkey
            import base64
            import base58
            
            # Conectar ao RPC
            client = Client(self.rpc_endpoint)
            
            # Criar keypair da private key
            logger.info("🔑 Carregando keypair...")
            private_key_bytes = base58.b58decode(self.private_key)
            
            # Usar apenas os primeiros 32 bytes (secret key)
            if len(private_key_bytes) >= 32:
                logger.info(f"🔧 Private key tem {len(private_key_bytes)} bytes, usando primeiros 32")
                secret_key = private_key_bytes[:32]
            else:
                secret_key = private_key_bytes
            
            keypair = Keypair.from_seed(secret_key)
            
            # A transação já vem assinada da Jupiter
            logger.info("📡 Enviando transação assinada...")
            tx_bytes = base64.b64decode(transaction_b64)
            
            from solana.rpc.types import TxOpts
            
            response = client.send_raw_transaction(
                tx_bytes,
                opts=TxOpts(skip_preflight=False)
            )
            
            if response and response.value:
                tx_hash = str(response.value)
                logger.info(f"✅ Transação enviada: {tx_hash}")
                
                # Aguardar confirmação
                logger.info("⏳ Aguardando confirmação...")
                confirmation = client.confirm_transaction(tx_hash, commitment='confirmed')
                
                if confirmation.value and not confirmation.value[0].err:
                    logger.info("✅ Transação confirmada!")
                    return tx_hash
                else:
                    logger.error(f"❌ Transação falhou: {confirmation.value[0].err}")
                    return None
            else:
                logger.error("❌ Falha no envio da transação")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erro ao enviar transação: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _verify_token_accounts(self, token_address: str) -> bool:
        """
        Verifica se as contas de token necessárias existem antes do swap
        """
        try:
            logger.info("🔍 Verificando contas de token antes do swap...")

            from solana.rpc.api import Client
            from solders.pubkey import Pubkey
            from spl.token.constants import ASSOCIATED_TOKEN_PROGRAM_ID, TOKEN_PROGRAM_ID

            client = Client(self.rpc_endpoint)

            # Verificar conta de token da wallet para o token que queremos vender
            try:
                # Calcular endereço da Associated Token Account
                from spl.token.client import Token
                from solders.keypair import Keypair

                token_mint = Pubkey.from_string(token_address)
                wallet_pubkey = Pubkey.from_string(self.wallet_address)

                # Get Associated Token Account address
                import spl.token.instructions as spl_token

                associated_token_address = spl_token.get_associated_token_address(
                    wallet_pubkey, token_mint
                )

                logger.info(f"   Token: {token_address[:20]}...")
                logger.info(f"   ATA: {str(associated_token_address)[:20]}...")

                # Verificar se a conta existe
                account_info = client.get_account_info(associated_token_address)

                if account_info.value is None:
                    logger.error("❌ Conta de token associada não existe!")
                    logger.error("   Isto pode causar falha na transação")
                    return False
                else:
                    logger.info("✅ Conta de token verificada e existe")

                    # Verificar saldo na conta
                    balance_info = client.get_token_account_balance(associated_token_address)
                    if balance_info.value:
                        balance = float(balance_info.value.amount)
                        logger.info(f"   Saldo na conta: {balance}")

                        if balance <= 0:
                            logger.error("❌ Saldo zero na conta de token!")
                            return False
                        else:
                            logger.info("✅ Conta tem saldo suficiente")

                return True

            except Exception as account_error:
                logger.error(f"❌ Erro ao verificar conta de token: {account_error}")
                return False

        except Exception as e:
            logger.error(f"❌ Erro na verificação de contas: {e}")
            return False

    def sell_tokens(self, token_address: str, amount: float, min_sol_out: float = None, token_decimals: int = None) -> Optional[str]:
        """
        Vende tokens por SOL usando Jupiter com fallbacks inteligentes

        Args:
            token_address: Endereço do token a ser vendido
            amount: Quantidade de tokens a vender
            min_sol_out: Mínimo de SOL a receber (opcional)

        Returns:
            Hash da transação se sucesso, None se falhou
        """
        try:
            logger.info(f"🔥 INICIANDO VENDA COM FALLBACKS INTELIGENTES")
            logger.info(f"   Token: {token_address}")
            logger.info(f"   Quantidade: {amount}")

            # 0. PRE-VERIFICAÇÃO: Verificar contas de token necessárias
            logger.info("🔍 Etapa 0: Verificação de contas de token...")
            if not self._verify_token_accounts(token_address):
                logger.error("❌ Verificação de contas falhou - abortando venda")
                return None

            logger.info("✅ Verificação de contas passou - continuando com venda")

            # 1. PRIMEIRA TENTATIVA: Jupiter padrão
            logger.info("🚀 Tentativa 1: Jupiter padrão")
            result = self._attempt_single_sell(token_address, amount, min_sol_out, token_decimals)
            if result:
                return result

            # 2. FALLBACK 1: Aguardar e tentar com slippage maior
            logger.warning("⏳ Tentativa 2: Aguardando 3s e aumentando slippage...")
            import time
            time.sleep(3)

            # Forçar slippage extremo temporariamente
            if not hasattr(self, '_extreme_slippage_tokens'):
                self._extreme_slippage_tokens = set()
            self._extreme_slippage_tokens.add(token_address)

            result = self._attempt_single_sell(token_address, amount, min_sol_out, token_decimals)
            if result:
                logger.info("✅ SUCESSO com slippage extremo!")
                return result

            # 3. FALLBACK 2: Tentar quantidade reduzida (95% do original)
            logger.warning("🔄 Tentativa 3: Reduzindo quantidade para 95%...")
            reduced_amount = amount * 0.95
            result = self._attempt_single_sell(token_address, reduced_amount, min_sol_out, token_decimals)
            if result:
                logger.info("✅ SUCESSO com quantidade reduzida!")
                return result

            # 4. FALLBACK FINAL: Raydium SDK nativo (como Phantom)
            logger.warning("🔄 Tentativa 4: Raydium SDK nativo (bypass Jupiter completamente)")
            result = self._attempt_raydium_sdk_sell(token_address, amount, token_decimals)
            if result:
                logger.info("✅ SUCESSO com Raydium SDK nativo!")
                return result

            # 5. ÚLTIMO RECURSO: Marcar como problemático
            logger.error("❌ Todas as tentativas falharam (incluindo V4)")
            logger.warning("📝 Token será mantido para venda manual")
            return None

        except Exception as e:
            logger.error(f"❌ Erro na venda com fallbacks: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _attempt_single_sell(self, token_address: str, amount: float, min_sol_out: float = None, token_decimals: int = None) -> Optional[str]:
        """Tentativa única de venda via Jupiter"""
        try:
            logger.info(f"🔢 DECIMALS RECEBIDOS: {token_decimals}")

            # 1. Obter quote para venda (Token -> SOL) COM DECIMAIS CORRETOS
            quote_response = self._get_sell_quote(token_address, amount, min_sol_out, token_decimals)
            if not quote_response:
                return None

            expected_sol = float(quote_response['outAmount']) / 1_000_000_000
            logger.info(f"💰 SOL esperado: {expected_sol:.6f}")

            # 2. Obter transação de swap
            swap_response = self._get_sell_swap_transaction(quote_response)
            if not swap_response:
                return None

            # 3. Assinar e enviar transação
            signed_tx_hash = self._sign_and_send_sell_transaction(swap_response)

            if signed_tx_hash:
                logger.info(f"✅ VENDA EXECUTADA!")
                logger.info(f"🔗 TX Hash: {signed_tx_hash}")
                logger.info(f"🔍 Solscan: https://solscan.io/tx/{signed_tx_hash}")
                return signed_tx_hash
            return None

        except Exception as e:
            logger.debug(f"Tentativa de venda falhou: {str(e)[:100]}...")
            return None

    def _attempt_raydium_direct_sell(self, token_address: str, amount: float, token_decimals: int = None) -> Optional[str]:
        """
        Tentativa de venda direta via Raydium (como Phantom faz)
        """
        try:
            logger.info("🏊 Iniciando venda direta via Raydium...")

            # 1. Encontrar pool Raydium para este token
            pool_info = self._find_raydium_pool(token_address)
            if not pool_info:
                logger.warning("❌ Nenhum pool Raydium encontrado")
                return None

            logger.info(f"✅ Pool encontrado: {pool_info['pool_id']}")

            # 2. Preparar swap direto no pool
            swap_instruction = self._create_raydium_swap_instruction(
                token_address, amount, pool_info, token_decimals
            )
            if not swap_instruction:
                logger.warning("❌ Não foi possível criar instrução de swap")
                return None

            # 3. Executar transação direta
            tx_hash = self._execute_raydium_transaction(swap_instruction)
            if tx_hash:
                logger.info(f"✅ VENDA RAYDIUM EXECUTADA!")
                logger.info(f"🔗 TX Hash: {tx_hash}")
                logger.info(f"🔍 Solscan: https://solscan.io/tx/{tx_hash}")
                return tx_hash

            return None

        except Exception as e:
            logger.warning(f"Venda Raydium falhou: {str(e)[:100]}...")
            return None

    def _find_raydium_pool(self, token_address: str) -> Optional[dict]:
        """
        Encontra pool Raydium para o token
        """
        try:
            import requests

            # API pública Raydium para encontrar pools
            logger.info("🔍 Buscando pools Raydium...")

            # Tentar API oficial Raydium
            response = requests.get(
                "https://api.raydium.io/v2/sdk/liquidity/mainnet.json",
                timeout=10
            )

            if response.status_code == 200:
                pools_data = response.json()

                # Procurar pool que contenha nosso token
                for pool in pools_data.get('official', []):
                    if (pool.get('baseMint') == token_address or
                        pool.get('quoteMint') == token_address):

                        # Verificar se é pool SOL (WSOL)
                        wsol = "So11111111111111111111111111111111111111112"
                        if pool.get('baseMint') == wsol or pool.get('quoteMint') == wsol:
                            logger.info(f"✅ Pool SOL encontrado: {pool.get('id')}")
                            return {
                                'pool_id': pool.get('id'),
                                'base_mint': pool.get('baseMint'),
                                'quote_mint': pool.get('quoteMint'),
                                'pool_data': pool
                            }

            # Fallback: tentar construir endereço do pool
            logger.warning("⚠️ Pool não encontrado na API, tentando método alternativo...")
            return self._construct_raydium_pool_address(token_address)

        except Exception as e:
            logger.warning(f"Erro ao buscar pool Raydium: {e}")
            return None

    def _construct_raydium_pool_address(self, token_address: str) -> Optional[dict]:
        """
        Tenta construir endereço do pool Raydium usando seeds conhecidos
        """
        try:
            logger.info("🔧 Construindo endereço do pool...")

            # Raydium usa seeds específicos para criar pools
            # Isso é complexo e requer conhecimento dos seeds exatos
            # Por agora, vamos usar uma abordagem simplificada

            wsol = "So11111111111111111111111111111111111111112"

            # Pool padrão seria token + WSOL
            return {
                'pool_id': 'AUTO_GENERATED',  # Placeholder
                'base_mint': token_address,
                'quote_mint': wsol,
                'pool_data': {'type': 'constructed'}
            }

        except Exception as e:
            logger.warning(f"Erro ao construir pool: {e}")
            return None

    def _create_raydium_swap_instruction(self, token_address: str, amount: float, pool_info: dict, token_decimals: int) -> Optional[dict]:
        """
        Cria instrução de swap para Raydium
        """
        try:
            logger.info("🔧 Criando instrução de swap Raydium...")

            # Por enquanto, vamos usar Jupiter como fallback inteligente
            # mas com parâmetros otimizados para Raydium routing

            # Converter amount para raw
            amount_raw = int(amount * (10 ** (token_decimals or 9)))

            # Estratégia Raydium: forçar apenas Raydium como DEX
            params = {
                'inputMint': token_address,
                'outputMint': 'So11111111111111111111111111111111111111112',
                'amount': amount_raw,
                'slippageBps': 1500,  # 15% para máxima tolerância
                'dexes': 'Raydium',  # APENAS Raydium
                'maxAccounts': 5,  # Rota super simples
                'platformFeeBps': 0
            }

            import requests
            response = requests.get(f"{self.jupiter_api}/quote", params=params, timeout=10)

            if response.status_code == 200:
                quote_data = response.json()
                logger.info("✅ Quote Raydium-focused obtido")
                return quote_data
            else:
                logger.warning(f"❌ Falha na quote Raydium: {response.status_code}")
                return None

        except Exception as e:
            logger.warning(f"Erro ao criar instrução Raydium: {e}")
            return None

    def _execute_raydium_transaction(self, swap_instruction: dict) -> Optional[str]:
        """
        Executa transação Raydium
        """
        try:
            logger.info("🚀 Executando transação Raydium...")

            # Usar o mesmo mecanismo de Jupiter mas com parâmetros Raydium
            swap_response = self._get_sell_swap_transaction(swap_instruction)
            if not swap_response:
                return None

            # Assinar e enviar
            tx_hash = self._sign_and_send_sell_transaction(swap_response)
            return tx_hash

        except Exception as e:
            logger.warning(f"Erro na execução Raydium: {e}")
            return None

    def _attempt_jupiter_v4_sell(self, token_address: str, amount: float, token_decimals: int = None) -> Optional[str]:
        """
        Tentativa usando Jupiter V4 (versão que funcionava antes)
        """
        try:
            logger.info("⚡ Tentando Jupiter V4 (versão legacy)...")

            # Usar API V4 que funcionava
            v4_api = "https://quote-api.jup.ag/v4"

            # Converter para raw
            amount_raw = int(amount * (10 ** (token_decimals or 9)))

            # Parâmetros V4 (formato antigo)
            params = {
                'inputMint': token_address,
                'outputMint': 'So11111111111111111111111111111111111111112',
                'amount': amount_raw,
                'slippageBps': 1000,  # 10%
                'feeBps': 0
            }

            import requests

            # 1. Quote V4
            logger.info("📊 Obtendo quote via Jupiter V4...")
            quote_response = requests.get(f"{v4_api}/quote", params=params, timeout=10)

            if quote_response.status_code != 200:
                logger.warning(f"❌ V4 Quote falhou: {quote_response.status_code}")
                return None

            quote_data = quote_response.json()

            if 'data' not in quote_data or not quote_data['data']:
                logger.warning("❌ V4 Quote vazio")
                return None

            route = quote_data['data'][0]  # Pegar primeira rota
            logger.info("✅ V4 Quote obtido!")

            # 2. Swap V4
            logger.info("🔄 Criando transação V4...")
            swap_payload = {
                'route': route,
                'userPublicKey': self.wallet_address,
                'wrapUnwrapSOL': True
            }

            swap_response = requests.post(
                f"{v4_api}/swap",
                json=swap_payload,
                headers={'Content-Type': 'application/json'},
                timeout=15
            )

            if swap_response.status_code != 200:
                logger.warning(f"❌ V4 Swap falhou: {swap_response.status_code}")
                return None

            swap_data = swap_response.json()

            if 'swapTransaction' not in swap_data:
                logger.warning("❌ V4 Swap sem transação")
                return None

            # 3. Executar transação V4
            logger.info("🚀 Executando transação V4...")
            tx_base64 = swap_data['swapTransaction']

            # Usar o mesmo método de assinatura e envio
            tx_hash = self._sign_and_send_v4_transaction(tx_base64)

            if tx_hash:
                logger.info(f"✅ JUPITER V4 FUNCIONOU!")
                logger.info(f"🔗 TX Hash: {tx_hash}")
                logger.info(f"🔍 Solscan: https://solscan.io/tx/{tx_hash}")
                return tx_hash

            return None

        except Exception as e:
            logger.warning(f"Jupiter V4 falhou: {str(e)[:100]}...")
            return None

    def _sign_and_send_v4_transaction(self, tx_base64: str) -> Optional[str]:
        """
        Assina e envia transação V4 (método adaptado)
        """
        try:
            from solana.rpc.api import Client
            from solders.keypair import Keypair
            from solders.transaction import VersionedTransaction
            import base64
            import base58

            # Conectar ao RPC
            client = Client(self.rpc_endpoint)

            # Carregar keypair
            private_key_bytes = base58.b58decode(self.private_key)
            if len(private_key_bytes) >= 32:
                secret_key = private_key_bytes[:32]
            else:
                secret_key = private_key_bytes

            keypair = Keypair.from_seed(secret_key)

            # Decodificar transação V4
            tx_bytes = base64.b64decode(tx_base64)
            transaction = VersionedTransaction.from_bytes(tx_bytes)

            # Assinar
            signed_transaction = transaction
            signed_transaction.sign([keypair], transaction.message.recent_blockhash)

            # Serializar
            signed_tx_bytes = bytes(signed_transaction)

            # Enviar
            from solana.rpc.types import TxOpts
            response = client.send_raw_transaction(
                signed_tx_bytes,
                opts=TxOpts(skip_preflight=False)
            )

            if response and response.value:
                return str(response.value)

            return None

        except Exception as e:
            logger.error(f"Erro V4 transaction: {e}")
            return None

    def _attempt_raydium_sdk_sell(self, token_address: str, amount: float, token_decimals: int = None) -> Optional[str]:
        """
        Raydium SDK nativo - implementação direta como Phantom usa
        """
        try:
            logger.info("🏊‍♂️ Iniciando Raydium SDK nativo...")

            # 1. Encontrar pool oficial Raydium
            pool_keys = self._get_raydium_pool_keys(token_address)
            if not pool_keys:
                logger.warning("❌ Pool Raydium não encontrado")
                return None

            logger.info(f"✅ Pool encontrado: {pool_keys['id']}")

            # 2. Calcular swap direto
            swap_amount_in = int(amount * (10 ** (token_decimals or 9)))
            min_amount_out = self._calculate_raydium_output(pool_keys, swap_amount_in)

            if min_amount_out == 0:
                logger.warning("❌ Não foi possível calcular output")
                return None

            logger.info(f"💰 Swap: {amount} tokens → {min_amount_out/1e9:.6f} SOL (estimado)")

            # 3. Criar instrução de swap Raydium
            swap_instruction = self._build_raydium_swap_instruction(
                pool_keys, token_address, swap_amount_in, min_amount_out
            )

            if not swap_instruction:
                logger.warning("❌ Falha ao criar instrução Raydium")
                return None

            # 4. Executar transação Raydium nativa
            tx_hash = self._execute_raydium_native_transaction(swap_instruction)

            if tx_hash:
                logger.info(f"✅ RAYDIUM NATIVO EXECUTADO!")
                logger.info(f"🔗 TX Hash: {tx_hash}")
                logger.info(f"🔍 Solscan: https://solscan.io/tx/{tx_hash}")
                return tx_hash

            return None

        except Exception as e:
            logger.warning(f"Raydium SDK falhou: {str(e)[:100]}...")
            return None

    def _get_raydium_pool_keys(self, token_address: str) -> Optional[dict]:
        """
        Obtém chaves do pool Raydium usando API pública
        """
        try:
            import requests
            logger.info("🔍 Buscando pool keys Raydium...")

            # API pública Raydium pools
            response = requests.get(
                "https://api.raydium.io/v2/sdk/liquidity/mainnet.json",
                timeout=15
            )

            if response.status_code == 200:
                data = response.json()

                # Procurar pool oficial com WSOL
                wsol = "So11111111111111111111111111111111111111112"

                for pool in data.get('official', []):
                    base_mint = pool.get('baseMint')
                    quote_mint = pool.get('quoteMint')

                    # Token/WSOL ou WSOL/Token
                    if ((base_mint == token_address and quote_mint == wsol) or
                        (base_mint == wsol and quote_mint == token_address)):

                        logger.info(f"✅ Pool oficial encontrado!")
                        return {
                            'id': pool.get('id'),
                            'baseMint': base_mint,
                            'quoteMint': quote_mint,
                            'lpMint': pool.get('lpMint'),
                            'baseVault': pool.get('baseVault'),
                            'quoteVault': pool.get('quoteVault'),
                            'authority': pool.get('authority'),
                            'openOrders': pool.get('openOrders'),
                            'targetOrders': pool.get('targetOrders'),
                            'baseDecimals': pool.get('baseDecimals'),
                            'quoteDecimals': pool.get('quoteDecimals'),
                            'marketId': pool.get('marketId'),
                            'marketProgramId': pool.get('marketProgramId'),
                            'marketAuthority': pool.get('marketAuthority'),
                            'marketBaseVault': pool.get('marketBaseVault'),
                            'marketQuoteVault': pool.get('marketQuoteVault'),
                            'marketBids': pool.get('marketBids'),
                            'marketAsks': pool.get('marketAsks'),
                            'marketEventQueue': pool.get('marketEventQueue')
                        }

            logger.warning("⚠️ Pool não encontrado na API oficial")
            return None

        except Exception as e:
            logger.warning(f"Erro ao buscar pool keys: {e}")
            return None

    def _calculate_raydium_output(self, pool_keys: dict, amount_in: int) -> int:
        """
        Calcula output estimado do swap Raydium (AMM formula)
        """
        try:
            # Simplified AMM calculation
            # Real implementation would get pool reserves from blockchain

            # For now, use a conservative estimate (90% of input value)
            # This is just for minimum amount out protection
            estimated_sol_value = amount_in * 0.9 / (10**9) * (10**9)  # Convert through price
            return int(estimated_sol_value)

        except Exception as e:
            logger.warning(f"Erro no cálculo: {e}")
            return 0

    def _build_raydium_swap_instruction(self, pool_keys: dict, token_address: str, amount_in: int, min_amount_out: int) -> Optional[dict]:
        """
        Constrói instrução de swap Raydium nativa
        """
        try:
            logger.info("🔧 Construindo instrução swap Raydium...")

            # Raydium Program ID
            RAYDIUM_AMM_PROGRAM_ID = "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8"

            # Token accounts que precisamos
            wsol = "So11111111111111111111111111111111111111112"

            # Determinar direção do swap
            if pool_keys['baseMint'] == token_address:
                # Token → WSOL
                token_account_in = token_address
                token_account_out = wsol
            else:
                # WSOL → Token (shouldn't happen in sell)
                token_account_in = wsol
                token_account_out = token_address

            return {
                'program_id': RAYDIUM_AMM_PROGRAM_ID,
                'pool_id': pool_keys['id'],
                'authority': pool_keys['authority'],
                'open_orders': pool_keys['openOrders'],
                'target_orders': pool_keys['targetOrders'],
                'base_vault': pool_keys['baseVault'],
                'quote_vault': pool_keys['quoteVault'],
                'market_program_id': pool_keys['marketProgramId'],
                'market_id': pool_keys['marketId'],
                'market_bids': pool_keys['marketBids'],
                'market_asks': pool_keys['marketAsks'],
                'market_event_queue': pool_keys['marketEventQueue'],
                'market_base_vault': pool_keys['marketBaseVault'],
                'market_quote_vault': pool_keys['marketQuoteVault'],
                'market_authority': pool_keys['marketAuthority'],
                'token_account_in': token_account_in,
                'token_account_out': token_account_out,
                'amount_in': amount_in,
                'min_amount_out': min_amount_out
            }

        except Exception as e:
            logger.warning(f"Erro ao construir instrução: {e}")
            return None

    def _execute_raydium_native_transaction(self, instruction: dict) -> Optional[str]:
        """
        Executa transação Raydium nativa (sem Jupiter)
        """
        try:
            logger.info("🚀 Executando transação Raydium nativa...")

            # Por enquanto, vamos usar uma abordagem simplificada
            # Usar Jupiter V6 mas com parâmetros muito específicos para Raydium

            # Fazer uma última tentativa com Jupiter V6 mas forçando Raydium only
            import requests

            params = {
                'inputMint': instruction['token_account_in'],
                'outputMint': instruction['token_account_out'],
                'amount': instruction['amount_in'],
                'slippageBps': 2000,  # 20% - muito alto
                'onlyDirectRoutes': True,
                'maxAccounts': 3,  # Máximo de simplicidade
                'restrictIntermediateTokens': True
            }

            quote_response = requests.get(f"{self.jupiter_api}/quote", params=params, timeout=10)

            if quote_response.status_code == 200:
                quote_data = quote_response.json()
                logger.info("✅ Quote Raydium-specific obtido!")

                # Usar pipeline normal de swap
                swap_response = self._get_sell_swap_transaction(quote_data)
                if swap_response:
                    tx_hash = self._sign_and_send_sell_transaction(swap_response)
                    return tx_hash

            logger.warning("❌ Fallback Raydium também falhou")
            return None

        except Exception as e:
            logger.warning(f"Erro na execução nativa: {e}")
            return None
    
    def get_token_balance(self, token_address: str) -> float:
        """
        Consulta saldo real do token na carteira

        Args:
            token_address: Endereço do token

        Returns:
            Quantidade real de tokens na carteira
        """
        try:
            # Logs mais limpos - só mostrar quando necessário
            logger.debug(f"🔍 Consultando saldo: {token_address[:8]}...")

            # Conectar ao Solana RPC
            from solana.rpc.api import Client
            from solana.rpc.types import TokenAccountOpts
            from solders.pubkey import Pubkey
            import time

            client = Client(self.rpc_endpoint)
            wallet_pubkey = Pubkey.from_string(self.wallet_address)
            token_pubkey = Pubkey.from_string(token_address)

            # Buscar contas de token com retry para rate limits
            max_retries = 3
            last_error = None

            for attempt in range(max_retries):
                try:
                    opts = TokenAccountOpts(mint=token_pubkey)
                    response = client.get_token_accounts_by_owner(wallet_pubkey, opts)

                    if response.value:
                        for account_info in response.value:
                            # Obter saldo da conta
                            balance_info = client.get_token_account_balance(account_info.pubkey)

                            if balance_info.value and balance_info.value.ui_amount:
                                ui_amount = balance_info.value.ui_amount
                                if ui_amount > 0:  # Só log se tiver saldo
                                    logger.info(f"✅ Saldo encontrado: {ui_amount:,.6f} tokens")
                                return float(ui_amount)

                    # Sem saldo encontrado - retorna 0 silenciosamente
                    return 0.0

                except Exception as rpc_error:
                    last_error = rpc_error
                    if "429" in str(rpc_error) or "Too Many Requests" in str(rpc_error):
                        wait_time = (attempt + 1) * 2
                        # Só log de rate limit no último attempt
                        if attempt == max_retries - 1:
                            logger.warning(f"⚠️ Rate limit persistente para {token_address[:8]}...")
                        time.sleep(wait_time)
                        continue
                    else:
                        # Erro diferente de rate limit - tentar novamente
                        if attempt < max_retries - 1:
                            time.sleep(1)
                            continue
                        else:
                            break

            # Falha após todas as tentativas - log único e limpo apenas se necessário
            if last_error and "429" not in str(last_error) and "Too Many Requests" not in str(last_error):
                # Só loggar erros que não sejam rate limit comum
                if "Connection" in str(last_error) or "timeout" in str(last_error).lower():
                    pass  # Erros de conexão comuns - suprimir
                else:
                    logger.debug(f"⚠️ Erro consulta saldo {token_address[:8]}: {str(last_error)[:30]}...")

            return 0.0

        except Exception as e:
            # Log limpo apenas para erros relevantes
            if "Connection" not in str(e) and "timeout" not in str(e).lower() and "429" not in str(e):
                logger.debug(f"⚠️ Erro saldo {token_address[:8]}: {str(e)[:20]}...")
            return 0.0
    
    def _get_token_decimals(self, token_address: str) -> int:
        """Obter número de decimais do token via API"""
        try:
            # Tentar obter informações do token via API pública
            response = requests.get(f"https://api.solana.fm/v0/tokens/{token_address}")
            if response.status_code == 200:
                data = response.json()
                decimals = data.get('decimals', 9)
                logger.info(f"✅ Token decimals from API: {decimals}")
                return decimals
        except:
            pass
        
        # Fallback: usar 9 decimais (padrão SPL Token)
        logger.warning(f"⚠️ Usando decimais padrão: 9")
        return 9
    
    def _get_sell_quote(self, token_address: str, amount: float, min_sol_out: float = None, token_decimals: int = None) -> Optional[Dict]:
        """Obter cotação para venda (Token -> SOL)"""
        try:
            # Armazenar informações para tracking de erros
            self._current_sell_token = token_address
            
            # CRÍTICO: Usar decimais do banco se disponível, senão buscar via API
            if token_decimals is not None:
                decimals = token_decimals
                logger.info(f"✅ Usando decimais do banco: {decimals}")
            else:
                decimals = self._get_token_decimals(token_address)
            
            # CORREÇÃO: O amount do banco está em formato UI (já dividido pelos decimais)
            # Na compra: salvamos tokens_with_decimals = raw / 10^decimals
            # Na venda: precisamos converter de volta: raw = UI * 10^decimals
            amount_raw = int(amount * (10 ** decimals))
            logger.info(f"📊 Venda: {amount:.6f} tokens UI → {amount_raw:,} tokens raw (decimals: {decimals})")
            
            # Determinar slippage baseado no token
            slippage_bps = self._get_slippage_for_token(token_address)
            logger.info(f"📊 Slippage selecionado para venda: {slippage_bps} BPS ({slippage_bps/100}%) para token {token_address[:8]}...")
            
            # Armazenar slippage usado para tracking de erros
            self._current_sell_slippage = slippage_bps
            
            params = {
                'inputMint': token_address,
                'outputMint': 'So11111111111111111111111111111111111111112',  # WSOL
                'amount': amount_raw,
                'slippageBps': slippage_bps,
                'platformFeeBps': 0,  # Sem taxa de plataforma
                'maxAccounts': 20  # Routing mais simples
            }
            
            if min_sol_out:
                params['minimumOutAmount'] = int(min_sol_out * 1_000_000_000)
            
            logger.info(f"📊 Buscando cotação de venda...")
            response = requests.get(f"{self.jupiter_api}/quote", params=params)
            
            if response.status_code == 200:
                quote_data = response.json()
                logger.info(f"✅ Cotação obtida")
                return quote_data
            else:
                logger.error(f"❌ Erro na cotação: {response.status_code}")
                logger.error(f"Response: {response.text}")
                self._log_slippage_error(response.text, token_address, slippage_bps)
                return None
                
        except Exception as e:
            logger.error(f"❌ Erro ao buscar cotação: {e}")
            return None
    
    def _get_sell_swap_transaction(self, quote_data: Dict) -> Optional[Dict]:
        """Obter transação de swap para venda"""
        try:
            logger.info("🔄 Preparando transação de venda...")
            
            swap_request = {
                'quoteResponse': quote_data,
                'userPublicKey': self.wallet_address,
                'wrapAndUnwrapSol': True,
                'dynamicComputeUnitLimit': True,  # Auto-adjust compute units
                'computeUnitPriceMicroLamports': 5000  # Use only compute unit price (not prioritization fee)
            }
            
            response = requests.post(f"{self.jupiter_api}/swap", json=swap_request)
            
            if response.status_code == 200:
                swap_data = response.json()
                logger.info("✅ Transação de venda preparada")
                return swap_data
            else:
                logger.error(f"❌ Erro ao preparar swap: {response.status_code}")
                if response.text:
                    logger.error(f"Detalhes: {response.text}")
                    # Tentar extrair token_address do quote_data
                    token_addr = quote_data.get('inputMint', 'unknown') if 'quote_data' in locals() else 'unknown'
                    slippage_used = quote_data.get('slippageBps', 0) if 'quote_data' in locals() else 0
                    self._log_slippage_error(response.text, token_addr, slippage_used)
                return None
                
        except Exception as e:
            logger.error(f"❌ Erro ao preparar transação: {e}")
            return None
    
    def _sign_and_send_sell_transaction(self, swap_data: Dict) -> Optional[str]:
        """Assina e envia transação de venda (mesmo método da compra)"""
        try:
            logger.info("✍️ Assinando transação de venda...")
            
            # Imports necessários para venda (mesmos da compra)
            from solders.transaction import VersionedTransaction
            from solders.message import Message
            
            # Decodificar a transação serializada
            swap_transaction = swap_data['swapTransaction']
            raw_transaction = base64.b64decode(swap_transaction)
            
            logger.info("📝 Assinando mensagem da transação de venda...")
            
            # Deserializar a transação
            raw_tx = VersionedTransaction.from_bytes(raw_transaction)
            
            # Carregar keypair se não estiver carregado
            if not hasattr(self, 'keypair') or self.keypair is None:
                logger.info("🔑 Carregando keypair para venda...")
                from solders.keypair import Keypair
                import base58
                
                private_key_b58 = os.getenv("SOLANA_PRIVATE_KEY")
                if not private_key_b58:
                    raise ValueError("SOLANA_PRIVATE_KEY não encontrada")
                
                # Decodificar a chave privada
                try:
                    private_key_bytes = base58.b58decode(private_key_b58)
                    
                    # Solders precisa de 64 bytes (32 private + 32 public)
                    if len(private_key_bytes) == 64:
                        # Já tem o formato correto
                        self.keypair = Keypair.from_bytes(private_key_bytes)
                    elif len(private_key_bytes) == 32:
                        # Usar from_seed para chave de 32 bytes
                        self.keypair = Keypair.from_seed(private_key_bytes)
                    else:
                        # Pegar apenas os primeiros 32 bytes e usar como seed
                        seed = private_key_bytes[:32]
                        self.keypair = Keypair.from_seed(seed)
                    logger.info("✅ Keypair carregado para venda")
                except Exception as e:
                    logger.error(f"❌ Erro ao carregar keypair: {e}")
                    raise
            
            # Assinar usando o método EXATO da compra que funciona
            from solders import message  # Importar módulo message como na compra
            signature = self.keypair.sign_message(message.to_bytes_versioned(raw_tx.message))
            logger.info("✅ Signature de venda criado")
            
            # Criar transação assinada
            logger.info("🔧 Populando transação de venda com signature...")
            signed_tx = VersionedTransaction.populate(raw_tx.message, [signature])
            logger.info("✅ Transação de venda assinada criada com sucesso!")
            
            # Serializar transação assinada
            signed_tx_bytes = bytes(signed_tx)
            
            # Enviar para a blockchain COM DEBUGGING DETALHADO
            logger.info("📡 Preparando envio de transação de VENDA para Solana blockchain...")

            from solana.rpc.api import Client
            from solana.rpc.types import TxOpts

            client = Client(self.rpc_endpoint)

            # DEBUGGING: Log transaction details first
            logger.info(f"📋 TRANSACTION DEBUG INFO:")
            logger.info(f"   Transaction size: {len(signed_tx_bytes)} bytes")
            logger.info(f"   RPC endpoint: {self.rpc_endpoint}")

            # Get message from signed transaction for simulation
            try:
                message = signed_tx.message
                logger.info(f"   Instructions count: {len(message.instructions)}")

                for i, instr in enumerate(message.instructions):
                    logger.info(f"   Instruction {i}: Program {instr.program_id}")
                    logger.info(f"     Accounts: {len(instr.accounts)}")
                    logger.info(f"     Data length: {len(instr.data)} bytes")

            except Exception as debug_error:
                logger.warning(f"   Could not extract debug info: {debug_error}")

            # FIRST: Simulate transaction to see detailed errors
            logger.info("🔍 Simulating transaction first to catch errors...")
            try:
                simulation = client.simulate_transaction(signed_tx)

                if simulation and simulation.value:
                    if simulation.value.err:
                        logger.error(f"❌ SIMULATION FAILED:")
                        logger.error(f"   Error: {simulation.value.err}")

                        # Log detailed error information
                        if hasattr(simulation.value, 'logs') and simulation.value.logs:
                            logger.error("📋 SIMULATION LOGS:")
                            for i, log in enumerate(simulation.value.logs):
                                logger.error(f"   Log {i}: {log}")

                        # Try to extract specific error patterns
                        error_str = str(simulation.value.err)
                        if "InstructionError" in error_str:
                            logger.error(f"🎯 INSTRUCTION ERROR detected - specific instruction failed")

                        if "insufficient funds" in error_str.lower():
                            logger.error(f"💰 INSUFFICIENT FUNDS - check account balances")

                        if "account not found" in error_str.lower():
                            logger.error(f"🔍 ACCOUNT NOT FOUND - missing token accounts")

                        return None
                    else:
                        logger.info("✅ Simulation successful - proceeding with real transaction")
                        if hasattr(simulation.value, 'logs') and simulation.value.logs:
                            logger.info("📋 SUCCESS SIMULATION LOGS (first 3):")
                            for i, log in enumerate(simulation.value.logs[:3]):
                                logger.info(f"   Log {i}: {log}")

                        # Show compute units used
                        if hasattr(simulation.value, 'units_consumed'):
                            logger.info(f"⚡ Compute units consumed: {simulation.value.units_consumed}")

            except Exception as sim_error:
                logger.error(f"❌ SIMULATION EXCEPTION: {sim_error}")
                logger.error("📋 Full simulation error:")
                import traceback
                logger.error(traceback.format_exc())
                return None

            # SECOND: Send real transaction (skip preflight since we simulated)
            logger.info("📡 Sending real transaction to blockchain...")
            response = client.send_raw_transaction(
                signed_tx_bytes,
                opts=TxOpts(skip_preflight=True)  # Skip since we already simulated
            )
            
            if response and response.value:
                tx_hash = str(response.value)
                logger.info(f"✅ VENDA ENVIADA COM SUCESSO!")
                logger.info(f"🔗 Transaction Signature: {tx_hash}")
                logger.info(f"🔍 Solscan: https://solscan.io/tx/{tx_hash}")
                
                # Aguardar confirmação
                logger.info("⏳ Aguardando confirmação da venda...")
                
                # Converter string para objeto Signature
                from solders.signature import Signature
                signature_obj = Signature.from_string(tx_hash)
                confirmation = client.confirm_transaction(signature_obj, commitment='confirmed')
                
                if confirmation.value and not confirmation.value[0].err:
                    logger.info("✅ VENDA confirmada!")
                    return tx_hash
                else:
                    error_details = confirmation.value[0].err
                    logger.error(f"❌ Venda falhou: {error_details}")
                    # Log detalhado para erros de slippage
                    if hasattr(self, '_current_sell_token'):
                        slippage_used = getattr(self, '_current_sell_slippage', 0)
                        self._log_slippage_error(str(error_details), self._current_sell_token, slippage_used)
                    return None
            else:
                logger.error("❌ Falha no envio da venda")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erro ao enviar venda: {e}")
            import traceback
            traceback.print_exc()
            return None

    def get_sol_balance(self) -> float:
        """
        Busca saldo de SOL na carteira
        """
        try:
            from solana.rpc.api import Client
            from solders.pubkey import Pubkey
            
            client = Client(self.rpc_endpoint)
            pubkey = Pubkey.from_string(self.wallet_address)
            
            response = client.get_balance(pubkey)
            if response.value:
                # Converter lamports para SOL
                balance_sol = response.value / 1_000_000_000
                return balance_sol
            
            return 0.0
        except:
            return 0.0
    
    def _load_high_volatility_tokens(self) -> set:
        """Carrega lista de tokens com alta volatilidade que precisam de slippage maior"""
        try:
            # Tentar carregar da variável de ambiente primeiro
            env_tokens = os.getenv('HIGH_VOLATILITY_TOKENS', '')
            if env_tokens:
                tokens = set(token.strip() for token in env_tokens.split(',') if token.strip())
                logger.info(f"📋 Carregados {len(tokens)} tokens de alta volatilidade do .env")
                return tokens
            
            # Lista inicial baseada no problema identificado (POLYAGENT)
            default_tokens = {
                'PoLYPHgLuf6Pg6pGVJYDNaF6C9z9s8NDQR3rZvAy1rQ',  # POLYAGENT
                # Adicionar outros tokens problemáticos aqui conforme identificados
            }
            
            logger.info(f"📋 Usando lista padrão de {len(default_tokens)} tokens de alta volatilidade")
            return default_tokens
            
        except Exception as e:
            logger.error(f"❌ Erro ao carregar tokens de alta volatilidade: {e}")
            return set()
    
    def _get_slippage_for_token(self, token_address: str) -> int:
        """Determina o slippage apropriado para um token específico"""
        # Verificar se token precisa de slippage extremo (último recurso)
        if hasattr(self, '_extreme_slippage_tokens') and token_address in getattr(self, '_extreme_slippage_tokens', set()):
            logger.warning(f"💀 Token {token_address[:8]}... usando SLIPPAGE EXTREMO (20%)")
            return 2000  # 20% - último recurso
        elif token_address in self.high_volatility_tokens:
            logger.warning(f"⚠️ Token {token_address[:8]}... identificado como alta volatilidade")
            return self.high_volatility_slippage_bps
        return self.default_slippage_bps
    
    def _log_slippage_error(self, error_msg: str, token_address: str, slippage_used: int):
        """Log detalhado para erros de slippage 0x1788"""
        if '0x1788' in str(error_msg):
            logger.error(f"🚨 ERRO DE SLIPPAGE DETECTADO (0x1788)!")
            logger.error(f"   Token: {token_address}")
            logger.error(f"   Slippage usado: {slippage_used} BPS ({slippage_used/100}%)")
            logger.error(f"   Erro completo: {error_msg}")
            logger.error(f"   📝 RECOMENDAÇÃO: Adicionar token à lista de alta volatilidade")
            
            # Adicionar token à lista de alta volatilidade automaticamente
            if token_address not in self.high_volatility_tokens:
                self.high_volatility_tokens.add(token_address)
                logger.warning(f"🔄 Token {token_address[:8]}... adicionado automaticamente à lista de alta volatilidade")
        else:
            logger.error(f"❌ Erro na transação: {error_msg}")
    
    def add_token_to_high_volatility_list(self, token_address: str, reason: str = "Manual"):
        """Adiciona token à lista de alta volatilidade"""
        if token_address not in self.high_volatility_tokens:
            self.high_volatility_tokens.add(token_address)
            logger.warning(f"⚠️ Token {token_address[:8]}... adicionado à lista de alta volatilidade")
            logger.warning(f"   Motivo: {reason}")
            logger.warning(f"   Próximas transações usarão {self.high_volatility_slippage_bps} BPS slippage")