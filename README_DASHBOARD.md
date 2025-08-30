# 🔥 Solana Hot Pools Dashboard

Uma interface React moderna e responsiva para visualizar as hot pools da Solana com análise detalhada de tokens em tempo real.

## ✨ Features

- **🔥 Hot Pools em Tempo Real** - Top 30 pools mais quentes da Solana
- **🪙 Análise Detalhada de Tokens** - Preço, variações, score de segurança
- **⚡ Interface Sem Refresh** - Clique em qualquer token para ver detalhes instantaneamente
- **📱 Design Responsivo** - Funciona perfeitamente em desktop e mobile
- **🎨 UI/UX Moderna** - Design com glassmorphism e animações fluidas
- **🔄 Auto-refresh** - Dados atualizados automaticamente

## 🏗️ Arquitetura

```
smart-currency-selector/
├── frontend/                # React + Webpack
│   ├── src/
│   │   ├── components/     # Componentes React
│   │   ├── hooks/          # Custom hooks
│   │   ├── services/       # API calls
│   │   ├── styles/         # CSS styles
│   │   └── utils/          # Utilities
│   ├── public/             # Static files
│   └── package.json        # Dependencies
├── backend/                # Python Flask API
│   ├── api/               # API routes
│   ├── services/          # Business logic
│   └── server.py          # Main server
└── scripts/               # Setup scripts
```

## 🚀 Quick Start

### 1. Configuração Inicial

```bash
# Execute o script de setup
./setup.sh

# Configure sua API key no .env
# DEXTOOLS_API_KEY=sua_api_key_aqui
```

### 2. Iniciar a Aplicação

```bash
# Inicia backend e frontend automaticamente
./start.sh
```

### 3. Acessar a Dashboard

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000

## 🔧 Instalação Manual

### Backend (Python Flask)

```bash
cd backend
pip3 install -r requirements.txt
python3 server.py
```

### Frontend (React)

```bash
cd frontend
npm install
npm run dev
```

## 📊 API Endpoints

### Hot Pools
```bash
GET /api/hot-pools?limit=30
```

### Token Analysis
```bash
GET /api/token/{token_address}
```

### Health Check
```bash
GET /api/health
```

## 🎨 Design Features

### **Glassmorphism UI**
- Fundos translúcidos com blur effect
- Bordas suaves e sombras elegantes
- Gradientes vibrantes

### **Interações Fluidas**
- Hover effects com transformações
- Loading states animados
- Transições suaves entre estados

### **Layout Responsivo**
- Grid adaptativo
- Mobile-first approach
- Componentes flexíveis

## 🔥 Funcionalidades da Interface

### **Panel de Hot Pools**
- Lista das top 30 pools rankadas
- Informações de DEX e par de tokens
- Seleção visual com feedback
- Scroll infinito com design customizado

### **Panel de Análise de Token**
- Header com logo e informações básicas
- Métricas de preço em tempo real
- Score de segurança visual
- Links sociais e detalhes técnicos

### **Sistema de Estados**
- Loading states com spinners
- Error handling elegante
- Empty states informativos
- Feedback visual para ações

## 📱 Responsividade

- **Desktop**: Layout side-by-side
- **Tablet**: Stacked layout com scroll
- **Mobile**: Interface otimizada para toque

## 🎯 Tecnologias Utilizadas

### Frontend
- **React 18** - Interface reativa
- **Webpack 5** - Module bundler
- **CSS3** - Styling avançado
- **Axios** - HTTP client

### Backend
- **Flask** - Web framework
- **Requests** - API calls
- **Python-dotenv** - Environment management
- **Flask-CORS** - Cross-origin requests

## 🔐 Configuração da API

1. Obtenha uma API key em: https://developer.dextools.io
2. Configure no arquivo `.env`:

```bash
DEXTOOLS_API_KEY=sua_api_key_aqui
DEXTOOLS_BASE_URL=https://public-api.dextools.io/standard/v2
```

## 🚀 Deploy

### Desenvolvimento
```bash
./start.sh
```

### Produção
```bash
# Frontend
cd frontend && npm run build

# Backend com gunicorn
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 backend.server:app
```

## 🔄 Auto-refresh

A aplicação atualiza automaticamente:
- Hot pools a cada 30 segundos
- Token analysis quando selecionado
- Estado da conexão com a API

## 🎨 Customização

### Temas
Modifique as cores em `frontend/src/styles/App.css`:

```css
:root {
  --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  --accent-color: #ff6b6b;
  --text-primary: #333;
}
```

### Limites
Ajuste os limites no código:
- Máximo de pools: 100
- Timeout de API: 10 segundos
- Rate limiting: 2 segundos

## 🐛 Troubleshooting

### Erro de API Key
```bash
❌ DEXTOOLS_API_KEY não encontrada no .env
💡 Configure sua API key no arquivo .env
```

### Porta em uso
```bash
❌ Port 3000 is already in use
💡 Kill the process or change port in package.json
```

### Timeout de API
```bash
⚠️ Aguardando 2.0s para evitar rate limit...
```

## 📈 Performance

- **Lazy loading** de componentes
- **Debounced API calls** para evitar spam
- **Memoized components** para otimização
- **Rate limiting** respeitando limites da API

## 🔮 Roadmap

- [ ] WebSocket para updates em tempo real
- [ ] Notificações push para alerts
- [ ] Favoritos e watchlist
- [ ] Comparador de tokens
- [ ] Gráficos de preço histórico
- [ ] Export de dados (CSV/JSON)

---

**Desenvolvido com ❤️ para a comunidade Solana** 🚀