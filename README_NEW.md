# 🤖 WhatsApp Agent - Sistema Inteligente de Atendimento

> Sistema completo de atendimento automatizado via WhatsApp com IA, agendamentos inteligentes e dashboard administrativo.

## 🚀 Visão Geral

O **WhatsApp Agent** é uma solução empresarial completa para atendimento automatizado via WhatsApp, desenvolvida com **FastAPI**, **Next.js**, **PostgreSQL** e **Redis**. Sistema robusto, escalável e pronto para produção.

## ✨ Funcionalidades Principais

### 🤖 **IA Conversacional**
- Respostas inteligentes com OpenAI GPT
- Processamento de linguagem natural
- Aprendizado contínuo baseado em interações

### 📱 **Integração WhatsApp**
- Meta Business API oficial
- Webhooks seguros e em tempo real
- Suporte a múltiplas mídias (texto, imagem, áudio)
- Status de entrega completo

### 📅 **Agendamentos Inteligentes**
- Sistema automático de disponibilidade
- Confirmações via WhatsApp
- Interface administrativa completa
- Sincronização com calendários

### 📊 **Dashboard & Analytics**
- Métricas em tempo real
- Relatórios automatizados
- Análise de performance
- Sistema de alertas

## 🏗️ Estrutura do Projeto

```
whats_agent/
├── 📱 **APLICAÇÃO**
│   ├── app/                  # Backend FastAPI
│   ├── nextjs_dashboard/     # Frontend Next.js  
│   ├── alembic/             # Migrações BD
│   └── config/              # Configurações
│
├── 📚 **DOCUMENTAÇÃO**
│   ├── documentation/       # Relatórios e docs
│   │   └── reports/         # Relatórios técnicos
│   └── docs/               # Documentação API
│
├── 🧪 **TESTES**
│   ├── testing/            # Testes organizados
│   ├── tests/              # Suite principal
│   └── nextjs_dashboard/e2e/ # Testes E2E
│
├── 🔧 **UTILITÁRIOS**
│   ├── utilities/          # Scripts e ferramentas
│   ├── scripts/           # Automação
│   └── backups/           # Backups
│
└── 🐳 **INFRAESTRUTURA**
    ├── docker-compose.yml  # Containers
    ├── prometheus/         # Monitoring  
    └── logs/              # Arquivos de log
```

## ⚡ Quick Start

### 1. **Configuração Inicial**
```bash
# Clonar repositório
git clone https://github.com/VANCIMJOAO/wppagent.git
cd whats_agent

# Configurar ambiente
cp .env.example .env
# Editar .env com suas credenciais
```

### 2. **Executar com Docker** (Recomendado)
```bash
# Iniciar todos os serviços
docker-compose up -d

# Aplicar migrações
docker-compose exec app alembic upgrade head
```

### 3. **Executar em Desenvolvimento**
```bash
# Backend
pip install -r requirements.txt
python -m app.main

# Frontend
cd nextjs_dashboard
npm install && npm run dev
```

## 🧪 Testes

### **Testes Backend**
```bash
# Todos os testes
pytest

# Testes específicos  
python testing/test_appointments_api.py
```

### **Testes E2E (Frontend)**
```bash
# Executar testes críticos
./utilities/run-critical-e2e-tests.sh

# Interface visual
cd nextjs_dashboard && npx playwright test --ui
```

## 🔧 Utilitários

### **Scripts Disponíveis**
```bash
# Análise de esquema BD
python utilities/analyze_schema_inconsistencies.py

# Demo de cache
python utilities/demo_cache_invalidation.py

# Relatório de performance
./utilities/e2e-implementation-report.sh
```

## 📊 Monitoramento

### **Métricas Disponíveis**
- **Performance**: Tempo de resposta, throughput
- **Qualidade**: Taxa de sucesso, erros
- **Negócio**: Conversões, satisfação
- **Sistema**: CPU, memória, disco

### **Ferramentas**
- **Prometheus**: Coleta de métricas
- **Grafana**: Visualização (configurar separadamente)
- **Logs**: Centralizados em `/logs`

## 🚀 Deploy em Produção

### **Railway** (Recomendado)
```bash
# Deploy automático via GitHub
# Conectar repositório ao Railway
# Configurar variáveis de ambiente
```

### **Docker Deploy**
```bash
# Build da imagem
docker build -t whatsapp-agent .

# Deploy com compose
docker-compose -f docker-compose.prod.yml up -d
```

## 🔐 Segurança

### **Implementado**
- ✅ Autenticação JWT com refresh tokens
- ✅ Rate limiting por IP
- ✅ Validação de entrada robusta  
- ✅ Criptografia de dados sensíveis
- ✅ Headers de segurança (CSP, HSTS)
- ✅ Sistema RBAC completo

### **Configurações**
```env
# .env
JWT_SECRET_KEY=your-super-secret-key
REDIS_URL=redis://localhost:6379
DATABASE_URL=postgresql://user:pass@localhost/db
```

## 📚 Documentação

### **Disponível**
- 📋 **API Docs**: `/docs` (Swagger automático)
- 📊 **Relatórios**: `documentation/reports/`
- 🔧 **Configuração**: `documentation/next-steps.md`
- 📱 **Frontend**: `nextjs_dashboard/README.md`

### **Relatórios Técnicos**
- Sistema de Alertas
- Cache e Performance  
- PWA e Mobile
- Testes E2E
- Sistema RBAC

## 🤝 Contribuição

### **Como Contribuir**
1. Fork o projeto
2. Criar branch: `git checkout -b feature/nova-funcionalidade`
3. Commit: `git commit -m 'feat: adicionar nova funcionalidade'`
4. Push: `git push origin feature/nova-funcionalidade`
5. Abrir Pull Request

### **Padrões**
- **Commits**: Conventional Commits
- **Código**: Black + isort para Python
- **Testes**: Cobertura > 80%
- **Docs**: Atualizar sempre

## 📈 Roadmap

### **Próximas Versões**
- [ ] Integração com mais canais (Telegram, Instagram)
- [ ] IA ainda mais avançada
- [ ] Sistema de filas avançado
- [ ] Mobile app nativo
- [ ] Marketplace de plugins

## 📞 Suporte

### **Contato**
- 📧 **Email**: suporte@whatsappagent.com
- 💬 **WhatsApp**: +55 11 99999-9999
- 🐛 **Issues**: GitHub Issues
- 📚 **Wiki**: GitHub Wiki

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para detalhes.

---

## 🏆 Status do Projeto

### **Implementações Concluídas** ✅
- ✅ **Backend Completo** - FastAPI com todas as APIs
- ✅ **Frontend Responsivo** - Next.js dashboard
- ✅ **Sistema de Autenticação** - JWT + 2FA + RBAC  
- ✅ **Banco de Dados** - PostgreSQL com índices otimizados
- ✅ **Cache Redis** - Performance e sessões
- ✅ **Testes E2E** - Playwright com 40+ cenários
- ✅ **Monitoramento** - Prometheus + logs
- ✅ **Deploy Railway** - Produção funcionando
- ✅ **PWA Offline** - Funciona sem internet
- ✅ **Mobile Responsive** - Otimizado para celular

### **Qualidade Garantida** 🎯
- ✅ **Cobertura de Testes**: 100% dos fluxos críticos
- ✅ **Performance**: < 2s tempo de resposta
- ✅ **Segurança**: Todas as boas práticas
- ✅ **Documentação**: Completa e atualizada
- ✅ **Estrutura**: Organizada e profissional

**Status Atual**: 🚀 **PRONTO PARA PRODUÇÃO**

---

<div align="center">

**Desenvolvido com ❤️ para revolucionar o atendimento via WhatsApp**

[![Deploy](https://img.shields.io/badge/Deploy-Railway-black)](https://railway.app)
[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![Next.js](https://img.shields.io/badge/Next.js-14-black)](https://nextjs.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue)](https://postgresql.org)
[![Redis](https://img.shields.io/badge/Redis-7-red)](https://redis.io)

</div>
