#!/bin/bash

# Script simplificado para configurar Railway via CLI
# Focado especificamente nos serviços já criados

set -e

echo "🚀 Configuração Simplificada Railway"
echo "===================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}ℹ️ Sua URL já foi configurada: wppagent-production.up.railway.app${NC}"
echo ""

# Generate password
GRAFANA_PASSWORD=$(openssl rand -base64 32)

echo "🔧 Vou te ajudar a configurar manualmente no Railway..."
echo ""

# Create detailed instructions
cat > RAILWAY_STEP_BY_STEP.md << EOF
# 🚀 Configuração Railway Passo a Passo

## ✅ Sua aplicação já foi identificada:
**URL**: https://wppagent-production.up.railway.app/

## 📊 Configuração do PROMETHEUS

### 1. Acesse seu projeto Prometheus no Railway Dashboard

### 2. Vá na aba "Variables" e adicione:
\`\`\`
PROMETHEUS_RETENTION_TIME=15d
PORT=9090
\`\`\`

### 3. Vá na aba "Settings" → "Source":
- Conecte ao repositório: **VANCIMJOAO/wppagent**
- Branch: **main**

### 4. Vá na aba "Settings" → "Deploy":
- **Root Directory**: \`/\` (raiz)
- **Build Command**: (deixe vazio)
- **Start Command**: (deixe vazio)
- **Dockerfile Path**: \`Dockerfile.prometheus\`

### 5. Clique em "Deploy"

---

## 📈 Configuração do GRAFANA

### 1. Acesse seu projeto Grafana no Railway Dashboard  

### 2. Vá na aba "Variables" e adicione:
\`\`\`
GF_SECURITY_ADMIN_PASSWORD=$GRAFANA_PASSWORD
GF_INSTALL_PLUGINS=grafana-piechart-panel
GF_SERVER_ROOT_URL=https://\${RAILWAY_PUBLIC_DOMAIN}
GF_SECURITY_ALLOW_EMBEDDING=true
GF_AUTH_ANONYMOUS_ENABLED=false
PORT=3000
\`\`\`

### 3. Vá na aba "Settings" → "Source":
- Conecte ao repositório: **VANCIMJOAO/wppagent**
- Branch: **main**

### 4. Vá na aba "Settings" → "Deploy":
- **Root Directory**: \`/\` (raiz)
- **Build Command**: (deixe vazio)
- **Start Command**: (deixe vazio)
- **Dockerfile Path**: \`Dockerfile.grafana\`

### 5. Clique em "Deploy"

---

## 🔑 CREDENCIAIS

### Grafana:
- **Usuário**: admin
- **Senha**: \`$GRAFANA_PASSWORD\`

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
- Login: admin / $GRAFANA_PASSWORD
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

Gerado em: $(date)
EOF

# Fix the prometheus config (remove trailing slash)
sed -i 's|wppagent-production.up.railway.app/|wppagent-production.up.railway.app|g' prometheus/prometheus-railway.yml

echo -e "${GREEN}✅ Arquivo de configuração corrigido${NC}"

# Create commit script
cat > commit_and_deploy.sh << EOF
#!/bin/bash
echo "🚀 Enviando configurações para GitHub..."
git add .
git commit -m "fix: Railway configuration for Prometheus and Grafana

- Fixed prometheus-railway.yml target URL  
- Added step-by-step Railway configuration guide
- Generated secure Grafana password: HIDDEN
- Ready for Railway deployment via web interface

App URL: wppagent-production.up.railway.app
Prometheus config: prometheus/prometheus-railway.yml
Grafana config: grafana/ directory"

git push origin main
echo ""
echo "✅ Configurações enviadas para o GitHub!"
echo "🌐 Agora siga as instruções em RAILWAY_STEP_BY_STEP.md"
EOF

chmod +x commit_and_deploy.sh

echo ""
echo "🎉 Configuração Preparada!"
echo "========================="
echo ""
echo -e "${GREEN}📋 Instruções detalhadas:${NC} RAILWAY_STEP_BY_STEP.md"
echo -e "${GREEN}🔑 Senha do Grafana:${NC} $GRAFANA_PASSWORD"
echo ""
echo -e "${YELLOW}📤 Próximos passos:${NC}"
echo "1. ./commit_and_deploy.sh  (enviar para GitHub)"
echo "2. Abrir Railway Dashboard no navegador"
echo "3. Seguir RAILWAY_STEP_BY_STEP.md"
echo ""
echo -e "${BLUE}🔗 URLs importantes:${NC}"
echo "- Sua app: https://wppagent-production.up.railway.app/"
echo "- Metrics: https://wppagent-production.up.railway.app/metrics"
echo ""
echo "⚡ Configuração local concluída! Execute o commit_and_deploy.sh"
