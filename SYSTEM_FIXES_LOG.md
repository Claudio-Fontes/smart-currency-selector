# Sistema de Trading - Log de Correções Importantes
*Data: 2025-09-05*

## 🔴 PROBLEMAS CRÍTICOS CORRIGIDOS

### 1. ERRO DE VENDA - Vendendo Quantidade Errada
**Problema:** Sistema estava vendendo TODO o saldo da carteira ao invés da quantidade específica da trade
- Trades 15 e 16 (Blunt): Comprou ~11.400 tokens mas vendeu ~22.800 (DOBRO!)
- **Arquivo:** `trade/services/sell_service.py`
- **Linha corrigida:** 156 (antiga linha 151)
- **Correção:** `sell_amount = min(buy_amount_original, real_balance)`

### 2. CÁLCULO DE PROFIT/LOSS INCORRETO
**Problema:** Cálculo distorcido quando vendia quantidade diferente da comprada
- **Arquivo:** `trade/services/sell_service.py`
- **Linhas:** 163-171
- **Correção:** Implementado cálculo proporcional para vendas parciais

### 3. STOP LOSS ATIVANDO CEDO DEMAIS
**Problema:** Vendia com -5% quando deveria ser -10%
- **Arquivo:** `trade/services/sell_service.py`
- **Função:** `_should_sell()`
- **Correção:** Verificação correta do stop loss em -10%

### 4. DUPLICAÇÃO DE TRADES
**Problema:** Sistema comprava o mesmo token múltiplas vezes em sequência
- **Arquivo:** `trade/services/buy_service.py`
- **Linha:** 91-102
- **Correção:** Adicionada verificação de 30 segundos para evitar duplicação

### 5. NÃO RECOMPRAVA TOKENS JÁ VENDIDOS
**Problema:** Monitor só comprava tokens NUNCA comprados antes
- **Arquivo:** `trade/services/trade_monitor.py`
- **Linha:** 143
- **Correção:** Mudou de `WHERE t.id IS NULL` para `WHERE t.id IS NULL AND t.status = 'OPEN'`

## 📊 PARÂMETROS DO SISTEMA

### Configurações de Trading
```
PROFIT_TARGET: +20%
STOP_LOSS: -10%
MAX_TRADE_AMOUNT: 0.05 SOL
AUTO_TRADING: Habilitado
MONITORING_INTERVAL: 60 segundos
MIN_SCORE_TO_BUY: 80
```

### Proteções Implementadas
- ✅ Não compra token com posição ABERTA
- ✅ Não compra mesmo token em 30 segundos (anti-duplicação)
- ✅ Vende apenas quantidade da trade específica
- ✅ Cálculo proporcional de P&L
- ✅ Logs detalhados para debug

## 🗄️ ESTRUTURA DO BANCO DE DADOS

### Tabela: trades
```sql
- id: ID da trade
- token_address: Endereço do token
- token_symbol: Símbolo
- buy_price: Preço de compra
- buy_amount: Quantidade comprada
- sell_price: Preço de venda
- sell_amount: Quantidade vendida
- status: OPEN/CLOSED
- profit_loss_percentage: % de lucro/prejuízo
- sell_reason: PROFIT_TARGET/STOP_LOSS
```

### Tabela: suggested_tokens
```sql
- id: UUID
- token_address: Endereço
- analysis_score: Score de análise (0-100)
- suggested_at: Momento da sugestão
```

### Tabela: trade_config
```sql
- auto_trading_enabled: true/false
- max_trade_amount_sol: 0.05
- profit_target_percentage: 20
- stop_loss_percentage: 10
```

## 🔧 SCRIPTS ÚTEIS

### Verificar tokens elegíveis para compra
```bash
python3 check_eligible_tokens.py
```

### Executar compras pendentes manualmente
```bash
python3 execute_pending_buys.py
```

### Testar correções do sistema
```bash
python3 test_sell_corrections.py
```

### Reiniciar monitor
```bash
pkill -f monitor_daemon.py && sleep 2 && python3 monitor_daemon.py &
```

## 📝 QUERIES ÚTEIS

### Ver últimas vendas
```sql
SELECT id, token_symbol, buy_price, sell_price, profit_loss_percentage, sell_reason 
FROM trades 
WHERE sell_time IS NOT NULL 
ORDER BY sell_time DESC 
LIMIT 5;
```

### Ver trades abertas
```sql
SELECT id, token_symbol, buy_price, buy_amount, buy_time 
FROM trades 
WHERE status = 'OPEN';
```

### Ver configuração atual
```sql
SELECT * FROM trade_config;
```

## ⚠️ PONTOS DE ATENÇÃO

1. **Sempre verificar saldo real** antes de vender
2. **Usar quantidade da trade específica** na venda
3. **Proteger contra duplicação** de compras
4. **Monitorar logs** para detectar problemas
5. **Testar mudanças** antes de aplicar em produção

## 🚀 STATUS ATUAL
- Sistema corrigido e funcionando
- 3 trades abertas sendo monitoradas (holo, Blunt, Troll)
- Monitor rodando em background
- Vendas automáticas em +20% ou -10%