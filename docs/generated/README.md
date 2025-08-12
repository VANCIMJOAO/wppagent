# 🤖 WhatsApp Agent - Sistema de Agendamentos

Sistema completo de agendamentos via WhatsApp com dashboard administrativo e inteligência artificial.

## 🚀 Instalação Rápida

```bash
# 1. Clonar e instalar
git clone <repository>
cd whats_agent
pip install -r requirements.txt

# 2. Configurar banco
./seed_db.sh
alembic upgrade head

# 3. Configurar .env (copiar de .env.example)
cp .env.example .env
# Editar .env com suas credenciais

# 4. Executar sistema
./run_dev.sh
```

## 📱 Acesso

- **Dashboard**: http://localhost:8502
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs

## 🔧 Configuração Mínima (.env)

```bash
# Banco PostgreSQL
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/whats_agent

# OpenAI (obrigatório)
OPENAI_API_KEY=sua_chave_openai

# Meta WhatsApp (obrigatório para produção)
META_ACCESS_TOKEN=seu_token_meta
META_VERIFY_TOKEN=seu_token_verificacao
META_PHONE_NUMBER_ID=seu_numero_id
```

## ✨ Funcionalidades

- 🤖 **Bot WhatsApp** com IA integrada
- 📅 **Agendamentos automáticos** via conversa natural
- 📊 **Dashboard completo** para gestão
- 👥 **Gestão de clientes** e histórico
- 🛠️ **Múltiplos serviços** configuráveis
- 📈 **Relatórios e métricas** em tempo real
- 🔐 **Sistema de autenticação** seguro

## 📖 Documentação Completa

Ver arquivo `SISTEMA_COMPLETO.md` para documentação detalhada, arquitetura e próximos passos.

## 🛠️ Stack Tecnológica

- **Backend**: FastAPI + SQLAlchemy + PostgreSQL
- **Frontend**: Streamlit Dashboard
- **IA**: OpenAI GPT-4
- **WhatsApp**: Meta Business API
- **Deploy**: Docker Ready

## 📞 Suporte

Sistema pronto para produção. Para customizações ou suporte, consulte a documentação completa.

---

**Desenvolvido para pequenas empresas automatizarem agendamentos via WhatsApp** 🚀
