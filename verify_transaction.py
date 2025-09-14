#!/usr/bin/env python3
"""
Verificar transação na blockchain
"""

from solana.rpc.api import Client
from solders.signature import Signature

def verify_transaction():
    """Verifica se a transação foi confirmada"""
    
    tx_signature = "3vLgRYMmu1t5zNR2NTXe9rVtSBFYiUi4q6QiEVLt3ZCaKUfZF1Sx8YeFtmAd4BgzUJVCueUEdnM1yqJFLBvqTowd"
    
    print(f"🔍 Verificando transação: {tx_signature}")
    
    try:
        client = Client("https://api.mainnet-beta.solana.com")
        
        # Converter string para Signature
        sig = Signature.from_string(tx_signature)
        
        # Obter detalhes da transação
        print("📡 Buscando detalhes na blockchain...")
        tx_info = client.get_transaction(
            sig, 
            encoding="json", 
            commitment="confirmed",
            max_supported_transaction_version=0
        )
        
        if tx_info and tx_info.value:
            transaction = tx_info.value
            meta = transaction.transaction.meta
            
            print(f"✅ TRANSAÇÃO ENCONTRADA NA BLOCKCHAIN!")
            print(f"🔗 Signature: {tx_signature}")
            
            # Status da transação
            if meta.err is None:
                print(f"✅ STATUS: SUCESSO")
            else:
                print(f"❌ STATUS: FALHA - {meta.err}")
                return False
            
            # Detalhes financeiros
            print(f"💰 Fee pago: {meta.fee / 1_000_000_000:.6f} SOL")
            
            # Logs de programa
            if meta.log_messages:
                print(f"\n📝 Logs da transação:")
                for i, log in enumerate(meta.log_messages[:10]):  # Mostrar apenas os primeiros 10
                    print(f"   {i+1}. {log}")
                if len(meta.log_messages) > 10:
                    print(f"   ... e mais {len(meta.log_messages) - 10} logs")
            
            # Mudanças nos balances
            if hasattr(meta, 'pre_balances') and hasattr(meta, 'post_balances'):
                print(f"\n💸 Mudanças de balance:")
                for i, (pre, post) in enumerate(zip(meta.pre_balances, meta.post_balances)):
                    if pre != post:
                        diff = (post - pre) / 1_000_000_000
                        print(f"   Conta {i}: {diff:+.6f} SOL")
            
            # Mudanças nos tokens
            if hasattr(meta, 'pre_token_balances') and hasattr(meta, 'post_token_balances'):
                pre_tokens = {tb.account_index: tb for tb in meta.pre_token_balances} if meta.pre_token_balances else {}
                post_tokens = {tb.account_index: tb for tb in meta.post_token_balances} if meta.post_token_balances else {}
                
                all_indices = set(pre_tokens.keys()) | set(post_tokens.keys())
                
                if all_indices:
                    print(f"\n🪙 Mudanças de tokens:")
                    for idx in all_indices:
                        pre_balance = int(pre_tokens[idx].ui_token_amount.amount) if idx in pre_tokens else 0
                        post_balance = int(post_tokens[idx].ui_token_amount.amount) if idx in post_tokens else 0
                        
                        if pre_balance != post_balance:
                            mint = post_tokens[idx].mint if idx in post_tokens else pre_tokens[idx].mint
                            decimals = post_tokens[idx].ui_token_amount.decimals if idx in post_tokens else pre_tokens[idx].ui_token_amount.decimals
                            
                            diff = post_balance - pre_balance
                            ui_diff = diff / (10 ** decimals)
                            
                            print(f"   Token {mint}: {ui_diff:+,.2f}")
            
            print(f"\n🎉 COMPRA CONFIRMADA NA BLOCKCHAIN!")
            return True
            
        else:
            print(f"❌ Transação não encontrada ou ainda não confirmada")
            return False
    
    except Exception as e:
        print(f"❌ Erro ao verificar: {e}")
        return False

if __name__ == "__main__":
    success = verify_transaction()
    if success:
        print("\n✅ VERIFICAÇÃO CONCLUÍDA COM SUCESSO!")
    else:
        print("\n⚠️ VERIFICAÇÃO INCONCLUSIVA")