# INFORMAÇÕES CRÍTICAS DO PROJETO

## DATABASE
**IMPORTANTE: Este projeto usa PostgreSQL, NÃO SQLite!**

### Configuração do PostgreSQL:
- Host: localhost
- Port: 5432
- User: lucia
- Password: lucia
- Database: cm_bot (CORRETO - não é cm_smart_bot!)

### Conexão ao banco:
```python
import psycopg2
from psycopg2.extras import RealDictCursor

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    user="lucia",
    password="lucia",
    database="cm_bot"  # CORRETO!
)
```

### Tabelas principais:
- trades (status: OPEN/CLOSED)
- NÃO existe tabela positions separada - usar trades com status='OPEN'
- wallet_sync (se existir)

## ESTRUTURA DO PROJETO
- Backend: Python com FastAPI
- Frontend: React
- Database: PostgreSQL
- Trading: Solana blockchain
- Wallet: 5cQfESQeA1XZQT6C6JA3E9J9Vg7jp1KT4ttj8Pmw5V4R

## SINCRONIZAÇÃO E GESTÃO DE POSIÇÕES

### Scripts de Sincronização:
1. **`sync_wallet_simple.py`** - Sincronização simplificada (RECOMENDADO)
   - Importa tokens com valor > $1 da carteira
   - Fecha posições que não estão mais na carteira
   - Usa método alternativo para evitar rate limits

2. **`sync_wallet_with_solscan.py`** - Com integração Solscan
   - Busca histórico de transações
   - Calcula preço médio real de compra
   - Mais completo mas pode ter rate limits

3. **`fix_duplicate_trades_auto.py`** - Consolidação de duplicatas
   - Consolida trades duplicadas do mesmo token
   - Mantém histórico correto

4. **`check_sync_fghp.py`** - Análise de problemas
   - Verifica duplicações
   - Mostra tokens não sincronizados

### Scripts de Verificação:
- `check_positions.py` - Monitor de posições abertas (usa trades com status='OPEN')
- `check_wallet_balance.py` - Verifica saldos na carteira
- `check_wallet_real.py` - Verifica tokens reais na blockchain

### Problemas Conhecidos e Soluções:

#### 1. Duplicação de Trades:
**Problema**: Múltiplas trades abertas para o mesmo token
**Solução**: Executar `python3 fix_duplicate_trades_auto.py`

#### 2. Tokens na carteira não aparecem na base:
**Problema**: Tokens com valor > $1 não são rastreados
**Solução**: Executar `python3 sync_wallet_simple.py`

#### 3. Rate Limits nas APIs:
**Problema**: Too Many Requests (429) ao consultar muitos tokens
**Solução**: Usar sync_wallet_simple.py com lista known_tokens

### Tokens Conhecidos:
```python
known_tokens = [
    "FgHpSsku7asGyTThooDmkKwmzy24ucUeyBrW9kLqpump",  # POLYAGENT
    # Adicionar outros tokens aqui
]
```

## COMANDOS IMPORTANTES
- Verificar posições: `python3 check_positions.py`
- Sincronizar carteira: `python3 sync_wallet_simple.py`
- Corrigir duplicatas: `python3 fix_duplicate_trades_auto.py`
- Start: `./start.sh`

## SOLANA E TRADING

### Configurações:
- RPC: https://api.mainnet-beta.solana.com
- Slippage padrão: 500 BPS (5%)
- Slippage alta volatilidade: 1000 BPS (10%)

### Serviços:
- DEXTools: Para preços e informações de tokens
- Solscan: Para histórico de transações (https://solscan.io/)
- Jupiter: Para execução de swaps

## NOTAS IMPORTANTES
- SEMPRE usar PostgreSQL (cm_bot), NUNCA SQLite
- Posições abertas = trades com status='OPEN'
- Não existe tabela 'positions' separada
- Para adicionar token manual: editar known_tokens em sync_wallet_simple.py
- Sincronização deve importar tokens > $1 USD
- Consolidar duplicatas antes de sincronizar