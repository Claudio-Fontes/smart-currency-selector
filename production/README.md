# 🐳 Smart Currency Selector - Production Setup

Este diretório contém a configuração completa para rodar o Smart Currency Selector em produção usando Docker.

## 🏗️ Arquitetura

O sistema é dividido em 4 containers independentes:

1. **Database** (`postgres:15-alpine`) - Banco PostgreSQL
2. **Backend** (`python:3.12-slim`) - API Python com Flask
3. **Frontend** (`nginx:alpine`) - Interface React servida pelo Nginx
4. **Monitor** (`python:3.12-slim`) - Sistema de trading automático

## 🚀 Quick Start

### 1. Configurar Environment

```bash
# Copiar o arquivo de exemplo
cp production/.env.example production/.env

# Editar com suas configurações
nano production/.env
```

### 2. Iniciar Sistema

```bash
# Dar permissão ao script
chmod +x production/scripts/deploy.sh

# Iniciar todos os serviços
./production/scripts/deploy.sh start
```

### 3. Acessar Dashboard

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5000/api
- **Database**: localhost:5432

## ⚙️ Comandos Disponíveis

```bash
# Gerenciamento de serviços
./production/scripts/deploy.sh start          # Iniciar sistema
./production/scripts/deploy.sh stop           # Parar sistema  
./production/scripts/deploy.sh restart        # Reiniciar sistema
./production/scripts/deploy.sh health         # Verificar saúde dos serviços

# Logs e monitoramento
./production/scripts/deploy.sh logs           # Ver logs de todos os serviços
./production/scripts/deploy.sh logs monitor   # Ver logs apenas do monitor
./production/scripts/deploy.sh status         # Ver status do trading

# Trading
./production/scripts/deploy.sh enable-trading  # Ativar trading automático
./production/scripts/deploy.sh disable-trading # Desativar trading automático

# Manutenção
./production/scripts/deploy.sh update         # Atualizar containers
```

## 🔧 Configuração Detalhada

### Variáveis de Environment (.env)

```bash
# Database
DB_USER=admin
DB_PASSWORD=sua_senha_segura

# APIs Externas
DEXTOOLS_API_KEY=sua_chave_dextools
TELEGRAM_BOT_TOKEN=token_do_seu_bot
TELEGRAM_CHAT_ID=id_do_seu_chat

# Solana
SOLANA_PRIVATE_KEY=sua_chave_privada_solana
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com

# Trading
PROFIT_TARGET_PERCENTAGE=20
STOP_LOSS_PERCENTAGE=10
AUTO_TRADING_ENABLED=false
```

### Portas Utilizadas

- **3000** - Frontend (Nginx)
- **5000** - Backend (Python/Flask)
- **5432** - Database (PostgreSQL)

### Volumes Docker

- `postgres_data` - Dados do PostgreSQL
- `app_logs` - Logs da aplicação

## 📊 Monitoramento

### Health Checks

Todos os containers têm health checks configurados:

```bash
# Verificar status
docker-compose ps

# Ver health checks
docker-compose exec backend curl http://localhost:5000/api/health
```

### Logs

```bash
# Logs em tempo real
docker-compose logs -f

# Logs específicos
docker-compose logs -f monitor
docker-compose logs -f backend
```

### Métricas de Trading

```bash
# Status do sistema
./production/scripts/deploy.sh status

# Conectar direto no banco
docker-compose exec database psql -U admin -d smart_currency
```

## 🔒 Segurança

### Configurações Implementadas

- Containers isolados em rede privada
- Nginx com headers de segurança
- Database com autenticação
- Logs estruturados
- Health checks automáticos

### Recomendações Adicionais

1. **Firewall**: Configurar firewall para expor apenas portas necessárias
2. **SSL/HTTPS**: Usar reverse proxy (Traefik/nginx) com certificados SSL
3. **Backup**: Configurar backup automático do volume `postgres_data`
4. **Monitoring**: Integrar com Grafana/Prometheus para monitoramento avançado

## 🛠️ Desenvolvimento vs Produção

### Diferenças Principais

| Aspecto | Desenvolvimento | Produção |
|---------|----------------|----------|
| Database | SQLite local | PostgreSQL container |
| Frontend | webpack-dev-server | Nginx otimizado |
| Backend | Flask debug | Gunicorn multi-worker |
| Logs | Console | Arquivo + volume |
| SSL | HTTP | HTTPS recomendado |
| Restart | Manual | Automático |

### Migração de Dados

Para migrar dados do desenvolvimento:

```bash
# Exportar dados do ambiente de dev
pg_dump desenvolvimento > backup.sql

# Importar no container de produção  
docker-compose exec database psql -U admin -d smart_currency < backup.sql
```

## 📁 Estrutura de Arquivos

```
production/
├── docker-compose.yml          # Definição dos serviços
├── .env.example                # Template de configuração
├── dockerfiles/                # Dockerfiles dos serviços
│   ├── Dockerfile.backend      # Backend Python
│   ├── Dockerfile.frontend     # Frontend React
│   └── Dockerfile.monitor      # Trading Monitor
├── config/                     # Configurações
│   ├── nginx.conf             # Configuração Nginx
│   └── default.conf           # Virtual host
├── database/                   # Schema do banco
│   └── init.sql               # Inicialização DB
├── scripts/                   # Scripts de automação
│   └── deploy.sh             # Script principal
└── README.md                  # Esta documentação
```

## 🐛 Troubleshooting

### Container não inicia

```bash
# Ver logs detalhados
docker-compose logs [nome_do_servico]

# Reconstruir imagem
docker-compose build --no-cache [nome_do_servico]
```

### Problemas de Conexão com Database

```bash
# Verificar se database está rodando
docker-compose exec database pg_isready -U admin

# Conectar manualmente
docker-compose exec database psql -U admin -d smart_currency
```

### Trading não funciona

```bash
# Verificar configuração
./production/scripts/deploy.sh status

# Ver logs do monitor
docker-compose logs monitor

# Verificar saldo SOL
# (implementar comando específico se necessário)
```

## 📞 Suporte

Para suporte e dúvidas:

1. Verificar logs dos containers
2. Usar o comando `health` para diagnóstico
3. Consultar documentação do projeto principal

---

## ⚡ Comandos Rápidos

```bash
# Setup inicial
cp production/.env.example production/.env
# [Editar .env]
./production/scripts/deploy.sh start

# Verificar status
./production/scripts/deploy.sh health
./production/scripts/deploy.sh status

# Ativar trading (apenas quando tudo estiver funcionando)
./production/scripts/deploy.sh enable-trading

# Monitorar
./production/scripts/deploy.sh logs monitor
```