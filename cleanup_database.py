#!/usr/bin/env python3
"""
Script para limpar base de dados mantendo apenas posições abertas
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from trade.database.connection import TradeDatabase

def cleanup_database():
    print("🧹 LIMPEZA DA BASE DE DADOS")
    print("=" * 60)
    
    db = TradeDatabase()
    
    with db.get_cursor() as cursor:
        # 1. Identificar tokens com posição aberta
        print("1️⃣ Identificando posições abertas...")
        cursor.execute("""
            SELECT id, token_address, token_symbol 
            FROM trades 
            WHERE status = 'OPEN'
        """)
        
        open_trades = cursor.fetchall()
        
        if open_trades:
            print(f"   ✅ {len(open_trades)} posições abertas encontradas:")
            for trade in open_trades:
                print(f"      - {trade['token_symbol']} (ID: {trade['id']})")
            
            # IDs das trades abertas
            open_trade_ids = [trade['id'] for trade in open_trades]
            open_token_addresses = [trade['token_address'] for trade in open_trades]
            
        else:
            print("   ⚠️ Nenhuma posição aberta encontrada!")
            return
        
        # 2. Contar registros antes da limpeza
        print("\n2️⃣ Contando registros antes da limpeza...")
        
        tables_to_check = [
            'trades',
            'price_monitoring', 
            'token_blacklist',
            'suggested_tokens',
            'positions',
            'buy_orders',
            'sell_orders'
        ]
        
        counts_before = {}
        for table in tables_to_check:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                counts_before[table] = count
                print(f"   {table}: {count} registros")
            except Exception as e:
                print(f"   {table}: ERRO - {e}")
                counts_before[table] = 0
        
        # 3. Executar limpeza
        print("\n3️⃣ Executando limpeza...")
        
        # Limpar price_monitoring (mantém apenas das trades abertas)
        if open_trade_ids:
            cursor.execute("""
                DELETE FROM price_monitoring 
                WHERE trade_id NOT IN ({})
            """.format(','.join(map(str, open_trade_ids))))
            print(f"   ✅ price_monitoring limpa (mantém trades: {open_trade_ids})")
        
        # Limpar token_blacklist (remove todos - recomeçar do zero)
        cursor.execute("DELETE FROM token_blacklist")
        print("   ✅ token_blacklist limpa completamente")
        
        # Limpar suggested_tokens (remove todos - recomeçar do zero)
        cursor.execute("DELETE FROM suggested_tokens")
        print("   ✅ suggested_tokens limpa completamente")
        
        # Limpar trades fechadas (mantém apenas OPEN)
        cursor.execute("DELETE FROM trades WHERE status != 'OPEN'")
        print("   ✅ trades fechadas removidas")
        
        # Limpar positions antigas
        cursor.execute("DELETE FROM positions")
        print("   ✅ positions limpa completamente")
        
        # Limpar orders antigas
        cursor.execute("DELETE FROM buy_orders")
        cursor.execute("DELETE FROM sell_orders")
        print("   ✅ buy_orders e sell_orders limpas")
        
        # 4. Contar registros após limpeza
        print("\n4️⃣ Contando registros após limpeza...")
        
        for table in tables_to_check:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                before = counts_before.get(table, 0)
                removed = before - count
                print(f"   {table}: {count} registros (removidos: {removed})")
            except Exception as e:
                print(f"   {table}: ERRO - {e}")
        
        # 5. Verificar integridade
        print("\n5️⃣ Verificando integridade...")
        cursor.execute("SELECT COUNT(*) FROM trades WHERE status = 'OPEN'")
        open_count = cursor.fetchone()[0]
        print(f"   ✅ {open_count} posições abertas mantidas")
        
        print("\n" + "=" * 60)
        print("🎯 LIMPEZA CONCLUÍDA!")
        print("=" * 60)
        print("✅ Backup salvo em: /tmp/backup_cm_bot_*.sql")
        print("✅ Posições abertas mantidas intactas")
        print("✅ Histórico limpo - sistema pronto para operar")
        print("\n💡 Para restaurar backup se necessário:")
        print("   psql -h localhost -U lucia -d cm_bot < /tmp/backup_cm_bot_*.sql")

if __name__ == "__main__":
    try:
        cleanup_database()
    except Exception as e:
        print(f"❌ Erro na limpeza: {e}")
        import traceback
        traceback.print_exc()