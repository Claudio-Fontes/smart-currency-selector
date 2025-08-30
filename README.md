# Smart Currency Selector

Cliente Python para análise completa de tokens usando a API da DEXTools. Inclui verificação de segurança, análise de holders, métricas de preço e tendências.

## 📁 Estrutura do Projeto

```
smart-currency-selector/
├── .env.example
├── .gitignore
├── requirements.txt
├── main.py
├── README.md
└── src/
    ├── __init__.py
    ├── client/
    │   ├── __init__.py
    │   └── dextools_client.py
    └── config/
        ├── __init__.py
        └── settings.py
```

## 🚀 Funcionalidades

- **Análise de Segurança**: Score da pool, liquidez bloqueada, auditoria
- **Métricas de Preço**: Preço atual, variação 24h, volume, liquidez
- **Análise de Holders**: Concentração dos principais detentores
- **Tendência de Preço**: Análise de movimento recente
- **Suporte Multi-chain**: Ethereum, BSC, Polygon, Arbitrum, Avalanche

## 📦 Instalação

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