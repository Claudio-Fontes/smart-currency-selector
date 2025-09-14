# 🚀 Deployment Guide - Smart Currency Selector

## 📋 Pré-requisitos

- Docker Engine 20.10+
- Docker Compose 2.0+
- 2GB RAM mínimo
- 10GB espaço em disco

## 🔧 Setup Inicial

### 1. Configurar Environment

```bash
# Entrar no diretório de produção
cd production/

# Copiar arquivo de configuração
cp .env.example .env

# Editar configurações (OBRIGATÓRIO)
nano .env
```

### 2. Configurar Variáveis Essenciais

No arquivo `.env`, configure obrigatoriamente:

```bash
# ⚠️ OBRIGATÓRIO - API DEXTools
DEXTOOLS_API_KEY=your_actual_api_key

# ⚠️ OBRIGATÓRIO - Chave privada Solana 
SOLANA_PRIVATE_KEY=your_wallet_private_key

# 🔒 Recomendado - Database seguro
DB_USER=admin
DB_PASSWORD=create_strong_password_here

# 📱 Opcional - Telegram notifications
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

## 🐳 Deploy

### Método 1: Script Automático (Recomendado)

```bash
# Dar permissão ao script
chmod +x scripts/deploy.sh

# Deploy completo
./scripts/deploy.sh start
```

### Método 2: Manual

```bash
# Construir imagens
docker-compose build

# Iniciar serviços
docker-compose up -d

# Verificar status
docker-compose ps
```

## ✅ Verificação

### 1. Verificar Serviços

```bash
# Status dos containers
./scripts/deploy.sh health

# Logs em tempo real
./scripts/deploy.sh logs
```

### 2. Testar Aplicação

- **Frontend**: http://localhost:3000
- **API Health**: http://localhost:5000/api/health
- **Hot Pools**: http://localhost:5000/api/hot-pools

### 3. Verificar Database

```bash
# Conectar no PostgreSQL
docker-compose exec database psql -U admin -d smart_currency

# Verificar tabelas criadas
\dt
```

## 🎯 Ativar Trading

⚠️ **IMPORTANTE**: Só ative o trading depois de verificar que tudo está funcionando!

```bash
# Verificar status atual
./scripts/deploy.sh status

# Ativar trading automático
./scripts/deploy.sh enable-trading

# Monitorar logs do trading
./scripts/deploy.sh logs monitor
```

## 📊 Monitoramento

### Logs

```bash
# Todos os serviços
docker-compose logs -f

# Serviço específico
docker-compose logs -f monitor
docker-compose logs -f backend
docker-compose logs -f database
```

### Status do Trading

```bash
# Status geral
./scripts/deploy.sh status

# Conectar no database para queries avançadas
docker-compose exec database psql -U admin -d smart_currency

# Ver trades abertas
SELECT token_symbol, buy_price, buy_time FROM trades WHERE status = 'OPEN';
```

## 🛠️ Comandos Úteis

```bash
# Reiniciar serviços
./scripts/deploy.sh restart

# Parar tudo
./scripts/deploy.sh stop

# Atualizar aplicação
./scripts/deploy.sh update

# Desativar trading
./scripts/deploy.sh disable-trading

# Ver estatísticas
./scripts/deploy.sh status
```

## 🔒 Segurança em Produção

### 1. Configurar Firewall

```bash
# Abrir apenas portas necessárias
sudo ufw allow 3000/tcp  # Frontend
sudo ufw allow 5000/tcp  # API (opcional, pode ser interno)
sudo ufw deny 5432/tcp   # Database (manter fechado)
```

### 2. HTTPS (Recomendado)

Para produção real, configure um reverse proxy com SSL:

```bash
# Exemplo com Nginx
upstream frontend {
    server localhost:3000;
}

upstream backend {
    server localhost:5000;
}

server {
    listen 443 ssl;
    server_name yourdomain.com;
    
    ssl_certificate /path/to/cert;
    ssl_certificate_key /path/to/key;
    
    location / {
        proxy_pass http://frontend;
    }
    
    location /api/ {
        proxy_pass http://backend;
    }
}
```

### 3. Backup Automático

```bash
# Criar script de backup
#!/bin/bash
docker-compose exec database pg_dump -U admin smart_currency > backup_$(date +%Y%m%d).sql

# Adicionar ao crontab (backup diário às 2:00)
0 2 * * * /path/to/backup_script.sh
```

## 🚨 Troubleshooting

### Container não inicia

```bash
# Ver logs detalhados
docker-compose logs [service_name]

# Reconstruir imagem
docker-compose build --no-cache [service_name]
docker-compose up -d [service_name]
```

### Database não conecta

```bash
# Verificar se está rodando
docker-compose exec database pg_isready -U admin

# Resetar database
docker-compose down
docker volume rm production_postgres_data
docker-compose up -d database
```

### Trading não funciona

```bash
# Verificar saldo SOL na carteira
# (implementar comando se necessário)

# Ver logs do monitor
docker-compose logs monitor

# Verificar configuração
docker-compose exec database psql -U admin -d smart_currency -c "SELECT * FROM trade_config;"
```

### API não responde

```bash
# Verificar logs do backend
docker-compose logs backend

# Testar diretamente
curl http://localhost:5000/api/health

# Reiniciar apenas o backend
docker-compose restart backend
```

## 🔄 Backup e Restore

### Backup

```bash
# Backup completo do database
docker-compose exec database pg_dump -U admin smart_currency > backup.sql

# Backup dos volumes (se necessário)
docker run --rm -v production_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz /data
```

### Restore

```bash
# Restore do database
cat backup.sql | docker-compose exec -T database psql -U admin -d smart_currency
```

## 📈 Scaling

### Aumentar Workers Backend

```bash
# Editar docker-compose.yml
environment:
  - WORKERS=4  # Adicionar esta linha

# Ou editar production/config/gunicorn.conf.py
workers = 4
```

### Monitoramento Avançado

Para produção empresarial, considere adicionar:

- Prometheus + Grafana
- ELK Stack (Elasticsearch, Logstash, Kibana)  
- Jaeger para tracing
- Healthchecks.io para monitoring

## 📞 Suporte

### Logs Importantes

1. **Backend**: `docker-compose logs backend`
2. **Monitor**: `docker-compose logs monitor` 
3. **Database**: `docker-compose logs database`
4. **Nginx**: `docker-compose logs frontend`

### Comandos de Diagnóstico

```bash
# Status geral
docker-compose ps
./scripts/deploy.sh health

# Uso de recursos
docker stats

# Espaço em disco
df -h
docker system df
```

---

## 🎉 Deployment Checklist

- [ ] Copiou e editou o arquivo `.env`
- [ ] Configurou `DEXTOOLS_API_KEY`  
- [ ] Configurou `SOLANA_PRIVATE_KEY`
- [ ] Executou `./scripts/deploy.sh start`
- [ ] Verificou que todos os containers estão rodando
- [ ] Testou frontend (http://localhost:3000)
- [ ] Testou API (http://localhost:5000/api/health)
- [ ] Verificou logs sem erros críticos
- [ ] **APENAS APÓS TESTES**: Ativou trading automático

**🚀 Seu Smart Currency Selector está pronto para produção!**