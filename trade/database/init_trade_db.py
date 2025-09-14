#!/usr/bin/env python3
"""
Inicializa as tabelas de trading no banco de dados
"""

import psycopg2
import os
import sys
from pathlib import Path

# Add parent path to import backend modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from trade.database.connection import TradeDatabase
from dotenv import load_dotenv

load_dotenv()

def init_trade_tables():
    """Cria as tabelas de trading no banco"""
    
    # Ler o arquivo SQL
    sql_file = Path(__file__).parent / 'create_tables.sql'
    with open(sql_file, 'r') as f:
        sql_commands = f.read()
    
    # Conectar ao banco
    db = TradeDatabase()
    
    try:
        with db.get_cursor() as cursor:
            # Executar os comandos SQL
            cursor.execute(sql_commands)
            print("✅ Tabelas de trading criadas com sucesso!")
            
            # Verificar tabelas criadas
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('trades', 'price_monitoring', 'trade_config')
                ORDER BY table_name;
            """)
            
            tables = cursor.fetchall()
            print("\n📊 Tabelas criadas:")
            for table in tables:
                print(f"   • {table['table_name']}")
            
            # Verificar configurações
            cursor.execute("SELECT config_key, config_value, description FROM trade_config ORDER BY config_key")
            configs = cursor.fetchall()
            
            print("\n⚙️ Configurações padrão:")
            for config in configs:
                print(f"   • {config['config_key']}: {config['config_value']}")
                print(f"     {config['description']}")
                
    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    init_trade_tables()