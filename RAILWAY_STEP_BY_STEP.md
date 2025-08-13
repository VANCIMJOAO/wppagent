# 🚀 Configuração Railway Passo a Passo

## ✅ Sua aplicação já foi identificada:
**URL**: https://wppagent-production.up.railway.app/

## 📊 Configuração do PROMETHEUS

### 1. Acesse seu projeto Prometheus no Railway Dashboard

### 2. Vá na aba "Variables" e adicione:
```
PROMETHEUS_RETENTION_TIME=15d
PORT=9090
```

### 3. Vá na aba "Settings" → "Source":
- Conecte ao repositório: **VANCIMJOAO/wppagent**
- Branch: **main**

### 4. Vá na aba "Settings" → "Deploy":
- **Root Directory**: `/` (raiz)
- **Build Command**: (deixe vazio)
- **Start Command**: (deixe vazio)
- **Dockerfile Path**: `Dockerfile.prometheus`

### 5. Clique em "Deploy"

---

## 📈 Configuração do GRAFANA

### 1. Acesse seu projeto Grafana no Railway Dashboard  

### 2. Vá na aba "Variables" e adicione:
```
GF_SECURITY_ADMIN_PASSWORD=ylCKddF9NBZMKKoszxt/v/ai3WOLOLy5YDWeOeYqDxM=
GF_INSTALL_PLUGINS=grafana-piechart-panel
GF_SERVER_ROOT_URL=https://${RAILWAY_PUBLIC_DOMAIN}
GF_SECURITY_ALLOW_EMBEDDING=true
GF_AUTH_ANONYMOUS_ENABLED=false
PORT=3000
```

### 3. Vá na aba "Settings" → "Source":
- Conecte ao repositório: **VANCIMJOAO/wppagent**
- Branch: **main**

### 4. Vá na aba "Settings" → "Deploy":
- **Root Directory**: `/` (raiz)
- **Build Command**: (deixe vazio)
- **Start Command**: (deixe vazio)
- **Dockerfile Path**: `Dockerfile.grafana`

### 5. Clique em "Deploy"

---

## 🔑 CREDENCIAIS

### Grafana:
- **Usuário**: admin
- **Senha**: `ylCKddF9NBZMKKoszxt/v/ai3WOLOLy5YDWeOeYqDxM=`

### URLs (após deploy):
- Prometheus: https://seu-prometheus.railway.app
- Grafana: https://seu-grafana.railway.app

---

## ✅ VERIFICAÇÃO

### 1. Aguarde 2-3 minutos após o deploy

### 2. Teste sua aplicação:
- Acesse: https://wppagent-production.up.railway.app/metrics
- Deve mostrar métricas do Prometheus

### 3. Teste o Prometheus:
- Acesse a URL do Prometheus
- Vá em Status → Targets
- O target 'whatsapp-agent' deve estar UP

### 4. Teste o Grafana:
- Acesse a URL do Grafana
- Login: admin / ylCKddF9NBZMKKoszxt/v/ai3WOLOLy5YDWeOeYqDxM=
- O dashboard deve carregar automaticamente

---

## 🔧 Se precisar de ajuda:

### Verificar logs:
1. No Railway Dashboard
2. Vá no projeto → Deployments  
3. Clique no deployment ativo
4. Veja os logs

### Problema comum - Target DOWN:
- Verifique se /metrics está funcionando na sua app
- Certifique-se que prometheus_client está instalado

Gerado em: ter 12 ago 2025 22:14:31 -03
