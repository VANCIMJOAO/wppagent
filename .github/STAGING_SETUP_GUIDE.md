# 🚀 Configuração do Ambiente de Staging

## 📋 Implementação Completa do Staging

Implementei um **ambiente de staging real** no seu pipeline CI/CD usando Railway. Agora você tem um workflow completo de desenvolvimento:

```
develop → Staging → main → Production
```

## 🔧 Configurações Necessárias

### 1. 🔑 GitHub Secrets (Repository Settings → Secrets)

Adicione estes secrets no GitHub:

```bash
# Railway
RAILWAY_TOKEN=<seu-railway-token>
RAILWAY_STAGING_PROJECT_ID=<id-do-projeto-staging>

# Database Staging
STAGING_DATABASE_URL=postgresql://user:password@host:port/staging_db
STAGING_REDIS_URL=redis://host:port/0
STAGING_SECRET_KEY=<chave-secreta-staging>

# APIs (mesmas de produção ou específicas de staging)
META_ACCESS_TOKEN=<token-meta>
PHONE_NUMBER_ID=<phone-id>
WEBHOOK_VERIFY_TOKEN=<webhook-token>
OPENAI_API_KEY=<openai-key>
```

### 2. 🌐 GitHub Variables (Repository Settings → Variables)

```bash
STAGING_URL=https://your-app-staging.railway.app
PRODUCTION_URL=https://your-app-production.railway.app
```

### 3. 🚂 Railway Setup

#### A. Criar Projeto Staging:
```bash
# No Railway dashboard
1. Criar novo projeto: "whatsapp-agent-staging"
2. Adicionar PostgreSQL database
3. Adicionar Redis
4. Configurar custom domain (opcional)
```

#### B. Obter Railway Token:
```bash
# No Railway dashboard → Account Settings → Tokens
1. Create New Token
2. Copiar token para RAILWAY_TOKEN secret
```

#### C. Obter Project ID:
```bash
# Na URL do projeto Railway
railway.app/project/[PROJECT-ID] ← copiar este ID
```

## 🔄 Como Funciona

### 📊 Fluxo Automatizado:

```mermaid
graph TD
    A[Push para develop] --> B[Tests & Security]
    B --> C[Build Docker Image]
    C --> D[Deploy to Staging]
    D --> E[Staging Health Check]
    E --> F[Manual Testing]
    F --> G[Merge to main]
    G --> H[Deploy to Production]
```

### 🎯 Features Implementadas:

1. **🚂 Railway CLI Integration**
   - Instalação automática
   - Autenticação com token

2. **🔧 Environment Setup**
   - Variáveis específicas para staging
   - Database e Redis separados

3. **🏥 Comprehensive Health Check**
   - Múltiplos endpoints testados
   - Aguarda aplicação estar pronta
   - Relatório detalhado de status

4. **📊 Deployment Summary**
   - Resumo no GitHub Actions
   - Links e informações úteis
   - Next steps para o desenvolvedor

5. **🎭 GitHub Environments**
   - Proteção do ambiente staging
   - URL tracking
   - Deployment history

## 🧪 Como Testar

### 1. Criar Branch Develop:
```bash
git checkout -b develop
git push origin develop
```

### 2. Fazer Push para Develop:
```bash
# Qualquer mudança no código
git add .
git commit -m "Test staging deployment"
git push origin develop
```

### 3. Acompanhar Pipeline:
- GitHub Actions executará automaticamente
- Deploy para staging acontecerá
- Health check validará aplicação

### 4. Testar Staging:
- Acessar URL do staging
- Fazer testes manuais
- Validar funcionalidades

### 5. Deploy Produção:
```bash
# Quando tudo estiver OK
git checkout main
git merge develop
git push origin main
```

## 📈 Benefícios

### ✅ **Qualidade**:
- Bugs detectados antes da produção
- Testes em ambiente real
- Validação de integrações

### ✅ **Segurança**:
- Deploy seguro com validação
- Rollback fácil se necessário
- Separação de ambientes

### ✅ **Eficiência**:
- Processo automatizado
- Feedback rápido
- Deploy confiável

### ✅ **Visibilidade**:
- Status claro do deployment
- Health checks detalhados
- Histórico de deployments

## 🚀 Próximos Passos

1. **Configure os secrets** no GitHub
2. **Crie o projeto staging** no Railway  
3. **Teste o primeiro deploy** com push para develop
4. **Documente a URL** de staging para a equipe
5. **Estabeleça processo** de teste em staging

---

**🎯 Resultado**: Ambiente de staging profissional pronto para uso!