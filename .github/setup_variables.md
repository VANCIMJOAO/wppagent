# 🔧 Configuração do Pipeline CI/CD

## 📋 Variables necessárias no GitHub

Configure no GitHub Repository: **Settings > Secrets and variables > Actions > Variables**

```bash
# Variables do Actions
STAGING_URL = https://staging.whatsapp-agent.com
PRODUCTION_URL = https://wppagent-production.up.railway.app
```

## 🔐 Secrets necessários no GitHub

Configure no GitHub Repository: **Settings > Secrets and variables > Actions > Secrets**

```bash
# Se o repositório for privado, adicione:
CODECOV_TOKEN = seu_token_codecov_aqui

# Token do GitHub já existe automaticamente como:
GITHUB_TOKEN = (automático)
```

## 🚀 Como configurar

### 1. Acesse seu repositório no GitHub

```
https://github.com/VANCIMJOAO/wppagent
```

### 2. Vá para Settings > Secrets and variables > Actions

### 3. Clique na aba "Variables" e adicione

- **Name:** `STAGING_URL`
- **Value:** `https://staging.whatsapp-agent.com`

- **Name:** `PRODUCTION_URL`
- **Value:** `https://wppagent-production.up.railway.app`

### 4. Se repositório privado, vá para aba "Secrets" e adicione

- **Name:** `CODECOV_TOKEN`
- **Value:** `seu_token_do_codecov`

## ✅ Validação

Após configurar, o pipeline terá:

- ✅ 0 erros de action não encontrada
- ✅ Variables de contexto funcionando
- ✅ Health checks executando corretamente
- ✅ Deploy para produção funcionando
- ✅ Pipeline 100% funcional

## 🎯 Environments

O pipeline funciona com 3 ambientes:

- **develop** → Deploy para Staging
- **main** → Deploy para Production
- **releases** → Deploy para Production com tag

## 🔄 Workflow

1. **Push para develop** → Testes + Deploy Staging + Health Check
2. **Push para main** → Testes + Build + Release automático
3. **Create Release** → Deploy para Production completo

## 📊 Monitoramento

- Coverage reports no Codecov
- Security scans com Trivy  
- Health checks automatizados
- Artifacts de deployment preservados
