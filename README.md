# 🤖 WhatsApp Agent - Sistema Inteligente de Atendimento

> Sistema completo de atendimento automatizado via WhatsApp com IA, integração com Meta Business API, banco de dados PostgreSQL e Redis para alta performance.

## 🚀 Visão Geral

O WhatsApp Agent é uma solução empresarial completa para atendimento automatizado via WhatsApp, desenvolvida com FastAPI, PostgreSQL, Redis e integração com Meta Business API. O sistema oferece conversas inteligentes, agendamentos automáticos, métricas em tempo real e arquitetura escalável.

## ✨ Principais Funcionalidades

### 🤖 Inteligência Artificial
- **IA Conversacional**: Respostas inteligentes com OpenAI GPT
- **Processamento de Linguagem Natural**: Compreensão de intenções
- **Aprendizado Contínuo**: Melhoria baseada em interações

### 📱 Integração WhatsApp
- **Meta Business API**: Integração oficial
- **Webhooks Seguros**: Recepção de mensagens em tempo real  
- **Múltiplos Tipos de Mídia**: Texto, imagens, áudio, documentos
- **Status de Entrega**: Controle completo de mensagens

### 📅 Sistema de Agendamentos
- **Agendamento Inteligente**: Disponibilidade automática
- **Confirmações Automatizadas**: Lembretes por WhatsApp
- **Gestão de Horários**: Interface administrativa
- **Integração com Calendários**: Sincronização automática

### 📊 Monitoramento e Métricas
- **Dashboard em Tempo Real**: Métricas de conversas
- **Análise de Performance**: Tempos de resposta
- **Relatórios Automatizados**: Insights de negócio
- **Alertas Inteligentes**: Notificações de problemas

## 🏗️ Arquitetura

### 🖥️ Backend
- **FastAPI**: Framework web moderno e rápido
- **PostgreSQL**: Banco de dados relacional robusto
- **Redis**: Cache e sessões para alta performance
- **Alembic**: Migrações de banco automatizadas

### 🔒 Segurança
- **Autenticação JWT**: Tokens seguros
- **2FA**: Autenticação de dois fatores
- **Encryption**: Dados sensíveis criptografados
- **Rate Limiting**: Proteção contra abuso
- **SSL/TLS**: Comunicação segura

### 🚀 DevOps & Deploy
- **Docker**: Containerização completa
- **Railway**: Deploy em nuvem
- **GitHub Actions**: CI/CD automatizado
- **Nginx**: Proxy reverso e SSL
- **Prometheus**: Monitoramento de métricas

## 📦 Instalação

### 🛠️ Pré-requisitos
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose
- Conta Meta Business

### 🚀 Setup Local

1. **Clone do repositório**
```bash
git clone https://github.com/VANCIMJOAO/wppagent.git
cd wppagent
```

2. **Ambiente virtual**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows
```

3. **Dependências**
```bash
pip install -r requirements.txt
```

4. **Configuração**
```bash
# Copiar arquivo de configuração
cp config/production.env .env

# Editar variáveis de ambiente
nano .env
```

5. **Database Setup**
```bash
# Inicializar migrações
alembic upgrade head

# Executar aplicação
uvicorn app.main:app --reload
```

### 🐳 Setup com Docker

```bash
# Construir e executar
docker-compose up -d

# Verificar status
docker-compose ps

# Logs
docker-compose logs -f
```

## ⚙️ Configuração

### 🔑 Variáveis de Ambiente

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/whatsapp_agent
REDIS_URL=redis://localhost:6379/0

# Meta WhatsApp
META_ACCESS_TOKEN=your_meta_token
PHONE_NUMBER_ID=your_phone_number_id
WEBHOOK_VERIFY_TOKEN=your_webhook_verify_token

# Security
SECRET_KEY=your_super_secret_key
JWT_SECRET=your_jwt_secret

# OpenAI
OPENAI_API_KEY=your_openai_api_key

# Application
ENVIRONMENT=production
DEBUG=false
HOST=0.0.0.0
PORT=8000
```

### 🌐 Webhook Configuration

Configure o webhook na Meta Business:
```
URL: https://your-domain.com/webhook
Verify Token: your_webhook_verify_token
```

## 🧪 Testes

### 🏃‍♂️ Executar Testes

```bash
# Testes completos
cd tests/
python run_super_test.py

# Testes específicos
python super_test_part1.py  # Infraestrutura
python super_test_part2.py  # Integração

# Testes rápidos
python quick_database_test.py
```

### 📊 Coverage

```bash
pytest --cov=app tests/
```

## 🚀 Deploy

### 🚂 Railway (Recomendado)

```bash
# Instalar Railway CLI
npm install -g @railway/cli

# Login
railway login

# Deploy
railway up
```

### 🐳 Docker Production

```bash
# Build da imagem
docker build -t whatsapp-agent .

# Executar em produção
docker run -d   --name whatsapp-agent   -p 8000:8000   --env-file .env   whatsapp-agent
```

## 📊 Monitoramento

### 📈 Métricas Disponíveis
- Número de conversas ativas
- Tempo médio de resposta
- Taxa de sucesso de mensagens
- Performance do banco de dados
- Uso de memória e CPU

### 🔍 Dashboard

Acesse `http://localhost:8000/dashboard` para visualizar:
- Métricas em tempo real
- Gráficos de performance  
- Status dos serviços
- Logs estruturados

## 🔧 Desenvolvimento

### 📁 Estrutura do Projeto

```
whats_agent/
├── app/                    # Aplicação principal
│   ├── auth/              # Sistema de autenticação
│   ├── models/            # Modelos de dados
│   ├── routes/            # Endpoints da API
│   ├── services/          # Lógica de negócio
│   ├── middleware/        # Middlewares
│   └── utils/             # Utilitários
├── tests/                 # Testes automatizados
├── scripts/               # Scripts de automação
├── config/                # Arquivos de configuração
├── alembic/              # Migrações do banco
└── docs/                 # Documentação
```

### 🎯 Padrões de Código

- **PEP 8**: Formatação Python
- **Type Hints**: Tipagem estática
- **Docstrings**: Documentação de funções
- **Tests**: Cobertura mínima de 80%

## 🤝 Contribuição

1. Fork do projeto
2. Criar branch de feature (`git checkout -b feature/AmazingFeature`)
3. Commit das mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

## 📄 API Documentation

### 🔗 Endpoints Principais

- `GET /health` - Status da aplicação
- `POST /webhook` - Recebimento de mensagens
- `GET /conversations` - Lista de conversas
- `POST /send-message` - Envio de mensagens
- `GET /metrics` - Métricas do sistema

Documentação completa: `http://localhost:8000/docs`

## 🔍 Troubleshooting

### ❓ Problemas Comuns

**Erro de conexão com WhatsApp:**
```bash
# Verificar token
curl -H "Authorization: Bearer $META_ACCESS_TOKEN" \
  "https://graph.facebook.com/v18.0/me"
```

**Problemas de banco:**
```bash
# Verificar conexão
python -c "from app.database import engine; print('DB OK')"
```

**Performance lenta:**
```bash
# Verificar Redis
redis-cli ping
```

## 📞 Suporte

- 📧 **Email**: suporte@whatsappagent.com
- 💬 **Discord**: [Link do servidor]
- 📚 **Docs**: [Documentação completa]
- 🐛 **Issues**: [GitHub Issues]

## 📝 Changelog

Veja [CHANGELOG.md](CHANGELOG.md) para histórico de versões.

## ⚖️ Licença

Este projeto está licenciado sob a Licença MIT - veja [LICENSE](LICENSE) para detalhes.

---

<div align="center">
  <p><strong>🤖 WhatsApp Agent</strong> - Desenvolvido com ❤️ para automatizar e melhorar o atendimento ao cliente</p>
  <p>
    <a href="#top">⬆️ Voltar ao topo</a>
  </p>
</div>
