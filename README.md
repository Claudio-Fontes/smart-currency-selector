# Smart Currency Selector

Sistema completo de análise e trading automático de tokens Solana. Inclui análise de pools, trading automático com stop loss/profit target, dashboard web e monitoramento em tempo real.

## 🏗️ **Ambientes Disponíveis**

### 🔧 **Desenvolvimento** (Atual)
- Frontend React + Backend Python Flask
- Database SQLite local  
- Trading monitor em processo único
- **Documentação**: Este README

### 🐳 **Produção Docker** (Novo!)
- 4 containers isolados (Frontend, Backend, Database, Monitor)
- PostgreSQL com alta disponibilidade
- Nginx otimizado + Gunicorn multi-worker
- Scripts de deploy automatizados
- **Documentação**: [DOCKER_PRODUCTION.md](DOCKER_PRODUCTION.md)

---

## 📁 Estrutura do Projeto

```
smart-currency-selector/
├── .env.example                    # Template de configuração
├── .gitignore                     
├── requirements.txt               # ✏️ Adicionado Flask, Gunicorn  
├── main.py                        # Análise CLI original
├── README.md                      # Esta documentação
├── DOCKER_PRODUCTION.md           # 🆕 Documentação Docker completa
├── .dockerignore                  # 🆕 Otimização Docker
├── start.sh                       # Script de desenvolvimento
├── frontend/                      # 🌐 Interface Web React
│   ├── package.json
│   ├── webpack.config.js
│   └── public/
│       ├── index.html            # Dashboard principal  
│       ├── app.html              # App alternativo
│       └── dashboard.html        # Dashboard detalhado
├── backend/                       # 🔧 API Python Flask
│   ├── server.py                 # Servidor principal
│   ├── api/
│   │   └── routes.py            # Rotas da API
│   └── services/                 # Serviços de negócio
│       ├── dextools_service.py
│       ├── token_analyzer.py
│       ├── performance_analyzer.py
│       ├── social_enhanced_service.py
│       └── telegram_notifier.py
├── trade/                         # 🤖 Sistema de Trading
│   ├── database/
│   │   └── connection.py         # PostgreSQL/SQLite
│   ├── services/
│   │   ├── buy_service.py        # Compras automáticas
│   │   ├── sell_service.py       # Vendas automáticas  
│   │   └── trade_monitor.py      # Monitor principal
│   └── utils/
│       └── solana_client.py      # Cliente Solana/Jupiter
├── production/                    # 🐳 Deploy Docker (NOVO!)
│   ├── docker-compose.yml        # Orquestração
│   ├── .env.example              # Config produção
│   ├── README.md                 # Guia de uso
│   ├── DEPLOYMENT.md             # Instruções deploy
│   ├── dockerfiles/              # Dockerfiles otimizados
│   │   ├── Dockerfile.backend
│   │   ├── Dockerfile.frontend  
│   │   └── Dockerfile.monitor
│   ├── config/                   # Configurações produção
│   │   ├── nginx.conf
│   │   ├── default.conf
│   │   └── gunicorn.conf.py
│   ├── database/
│   │   └── init.sql             # Schema automático
│   └── scripts/
│       └── deploy.sh            # 🚀 Script mágico
└── src/                          # 📊 Cliente original DEXTools
    ├── client/
    │   └── dextools_client.py
    └── config/
        └── settings.py
```

## 🚀 Funcionalidades

### 📊 **Análise de Tokens** (Original)
- **Análise de Segurança**: Score da pool, liquidez bloqueada, auditoria
- **Métricas de Preço**: Preço atual, variação 24h, volume, liquidez  
- **Análise de Holders**: Concentração dos principais detentores
- **Tendência de Preço**: Análise de movimento recente
- **Suporte Multi-chain**: Ethereum, BSC, Polygon, Arbitrum, Avalanche

### 🌐 **Dashboard Web** (Novo!)
- **Hot Pools**: Top 30 tokens em trending da DEXTools
- **Análise Visual**: Gráficos e métricas em tempo real
- **Interface Responsiva**: React otimizado para todos os dispositivos
- **Ticker Animado**: Tokens sugeridos com destaque visual

### 🤖 **Trading Automático** (Novo!)
- **Compra Automática**: Tokens sugeridos com score >= 80
- **Stop Loss**: Venda automática em -10% de prejuízo  
- **Profit Target**: Venda automática em +20% de lucro
- **Blacklist**: Tokens com stop loss não são recomprados
- **Monitoramento**: Verificação de preços a cada 30 segundos

### 🛡️ **Sistema de Proteção**
- **Anti-ciclo**: Cooldown de 2h após vendas lucrativas
- **Limite Diário**: Máximo 3 trades por token/dia  
- **Preço Real**: Busca preço de mercado no momento da compra
- **Verificação de Saldo**: Confirma tokens disponíveis antes da venda

### 🔔 **Notificações**
- **Telegram**: Alertas de compras e vendas automáticas
- **Logs Detalhados**: Histórico completo de todas as operações
- **Estatísticas**: Win rate, P&L médio, total de trades

### 🐳 **Deploy Produção** (Docker)
- **4 Containers**: Frontend, Backend, Database, Monitor isolados
- **Alta Disponibilidade**: Restart automático + Health checks
- **Escalabilidade**: Gunicorn multi-worker + PostgreSQL
- **Segurança**: Nginx otimizado + headers de proteção

## 🚀 Início Rápido

### 🐳 **Produção Docker (Recomendado)**
```bash
# 1. Configurar
cd production/
cp .env.example .env
# [Editar .env com DEXTOOLS_API_KEY e SOLANA_PRIVATE_KEY]

# 2. Deploy
./scripts/deploy.sh start

# 3. Acessar
# Frontend: http://localhost:3000  
# API: http://localhost:5000/api
```
📚 **Documentação completa**: [DOCKER_PRODUCTION.md](DOCKER_PRODUCTION.md)

### 🔧 **Desenvolvimento Local**
```bash
# 1. Instalar dependências
pip install -r requirements.txt
cd frontend && npm install

# 2. Configurar
cp .env.example .env
# [Editar .env com suas chaves]

# 3. Executar
chmod +x start.sh && ./start.sh
```

---

## 📦 Instalação Detalhada

```bash
# Clone o repositório
git clone <repo-url>
cd smart-currency-selector

# Instale as dependências
pip install -r requirements.txt

# Configure as variáveis de ambiente
cp .env.example .env
# Edite o arquivo .env e adicione sua API key da DEXTools
```

## 🔑 Configuração

1. Obtenha uma API key na [DEXTools](https://www.dextools.io/api)
2. Adicione as configurações no arquivo `.env`:
   ```
   DEXTOOLS_API_KEY=sua_api_key_aqui
   DEXTOOLS_BASE_URL=https://public-api.dextools.io/v2
   ```

## 📊 Como Usar

### Análise via Linha de Comando
```bash
# Análise com token como parâmetro
python main.py egy3LC9ndbxo8LzL8W3s8FzwS3H6gT7t73uUP2Mpump

# Especificar blockchain
python main.py egy3LC9ndbxo8LzL8W3s8FzwS3H6gT7t73uUP2Mpump -c solana

# Salvar resultados automaticamente
python main.py egy3LC9ndbxo8LzL8W3s8FzwS3H6gT7t73uUP2Mpump -c solana -s

# Modo não-interativo (sem prompts)
python main.py egy3LC9ndbxo8LzL8W3s8FzwS3H6gT7t73uUP2Mpump -c solana --no-interactive

# Modo interativo (sem parâmetros)
python main.py
```

### Parâmetros Disponíveis
- `token`: Endereço do token (obrigatório se não for modo interativo)
- `-c, --chain`: Blockchain (padrão: solana)
- `-s, --save`: Salvar resultados em arquivo automaticamente
- `--no-interactive`: Executar sem prompts interativos

### Uso Programático
```python
from dotenv import load_dotenv
from src.client import DEXToolsClient
from src.config import load_settings

load_dotenv()
settings = load_settings()
client = DEXToolsClient(
    settings['dextools']['api_key'],
    settings['dextools']['base_url']
)

# Análise completa
result = client.complete_analysis("eth", "0x...")

# Ou métodos individuais
holders = client.analyze_top_holders("eth", "0x...")
metrics = client.get_price_metrics("eth", "0x...")
security = client.security_check("eth", "0x...")
```

## 🛡️ Verificações de Segurança

- **Pool Score**: Avaliação de confiabilidade (0-100)
- **Liquidez Bloqueada**: Proteção contra rug pull
- **Auditoria**: Verificação de código por terceiros
- **Concentração de Holders**: Risco de manipulação

## 📈 Métricas Analisadas

- Preço atual em USD
- Variação percentual 24h
- Liquidez total em USD
- Volume de negociação 24h
- Tendência de preço (alta/baixa/lateral)

## 🔗 Blockchains Suportadas

- Ethereum (eth)
- Binance Smart Chain (bsc)
- Polygon (polygon)
- Arbitrum (arbitrum)
- Avalanche (avalanche)

## ⚠️ Limitações

- Requer API key da DEXTools (versão Standard)
- Rate limits aplicam conforme plano da API
- Alguns dados podem não estar disponíveis para todos os tokens

## 📝 Exemplo de Saída

```
🛡️ VERIFICAÇÃO DE SEGURANÇA:
  ✅ Pool Score alto (85/100) — boa reputação.
  🔒 Liquidez bloqueada — proteção contra rug pull.
  ✅ Token auditado — menor risco de vulnerabilidades.
  ⚠️ Concentração moderada: Top 10 holders detêm 55%.

📊 MÉTRICAS DO TOKEN:
  Preço (USD): $0.00123456
  Variação 24h: +5.67%
  Liquidez: $1,234,567.89
  Volume 24h: $987,654.32

📈 TENDÊNCIA DE PREÇO:
  📈 Tendência de alta
```

## 🤝 Contribuição

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou enviar pull requests.

## ⚖️ Disclaimer

Este software é apenas para fins educacionais e informativos. Não constitui aconselhamento financeiro. Sempre faça sua própria pesquisa (DYOR) antes de investir.

---

## 📋 Resumo Executivo

### ✅ **O que foi implementado:**

- ✅ **Análise CLI original** - Mantida funcionando
- ✅ **Dashboard Web React** - Interface moderna
- ✅ **API Backend Flask** - Endpoints organizados  
- ✅ **Trading Automático** - Compra/venda com IA
- ✅ **Sistema de Proteção** - Stop loss, blacklist, cooldowns
- ✅ **Notificações Telegram** - Alertas em tempo real
- ✅ **Deploy Docker** - Produção profissional com 4 containers
- ✅ **Documentação Completa** - Guias detalhados

### 🎯 **Como usar agora:**

1. **Para Produção**: `cd production/ && ./scripts/deploy.sh start`
2. **Para Desenvolvimento**: `./start.sh`
3. **Para CLI original**: `python main.py [token_address]`

### 📈 **Configurações de Trading:**
- **Profit Target**: +20% (configurável)
- **Stop Loss**: -10% (configurável)  
- **Score Mínimo**: 80/100 (configurável)
- **Intervalo**: 30 segundos (configurável)
- **Valor por Trade**: 0.05 SOL (configurável)

### 🔒 **Segurança Implementada:**
- Blacklist de tokens com stop loss
- Cooldown de 2h após lucro
- Limite de 3 trades/token/dia
- Verificação de saldo real
- Preço de mercado em tempo real

**🚀 Sistema completo pronto para uso em produção!**