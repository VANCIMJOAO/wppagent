#!/bin/bash

# Script para configurar Grafana e Prometheus que já existem no Railway
# Usage: ./configure_existing_railway_services.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    case $status in
        "SUCCESS")
            echo -e "${GREEN}✅ $message${NC}"
            ;;
        "FAIL")
            echo -e "${RED}❌ $message${NC}"
            ;;
        "WARNING")
            echo -e "${YELLOW}⚠️ $message${NC}"
            ;;
        "INFO")
            echo -e "${BLUE}ℹ️ $message${NC}"
            ;;
    esac
}

echo "🚀 Configurador para Serviços Railway Existentes"
echo "================================================"
echo ""

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    print_status "FAIL" "Railway CLI não encontrado"
    echo ""
    echo "Por favor, instale o Railway CLI primeiro:"
    echo "npm install -g @railway/cli"
    echo ""
    exit 1
fi

# Check authentication
print_status "INFO" "Verificando autenticação Railway..."
if ! railway whoami &> /dev/null; then
    print_status "INFO" "Fazendo login no Railway..."
    railway login
    
    if [ $? -ne 0 ]; then
        print_status "FAIL" "Falha na autenticação"
        exit 1
    fi
fi

print_status "SUCCESS" "Autenticado no Railway"

# Get user input
echo ""
echo "📋 Informações necessárias:"
echo ""

# Get WhatsApp Agent URL
echo "1. Qual é a URL da sua aplicação WhatsApp Agent?"
echo "   (Exemplo: minha-app.railway.app ou https://minha-app.railway.app)"
read -p "   URL da aplicação: " APP_URL

if [ -z "$APP_URL" ]; then
    print_status "FAIL" "URL da aplicação é obrigatória"
    exit 1
fi

# Clean up URL (remove https:// if present)
APP_URL=$(echo "$APP_URL" | sed 's|https://||g' | sed 's|http://||g')

echo ""
echo "2. Nome do projeto do Prometheus no Railway:"
read -p "   (pressione Enter se for 'prometheus'): " PROMETHEUS_PROJECT
PROMETHEUS_PROJECT=${PROMETHEUS_PROJECT:-prometheus}

echo ""
echo "3. Nome do projeto do Grafana no Railway:"
read -p "   (pressione Enter se for 'grafana'): " GRAFANA_PROJECT
GRAFANA_PROJECT=${GRAFANA_PROJECT:-grafana}

echo ""
print_status "INFO" "Configuração:"
echo "  - App URL: $APP_URL"
echo "  - Projeto Prometheus: $PROMETHEUS_PROJECT"
echo "  - Projeto Grafana: $GRAFANA_PROJECT"
echo ""

read -p "Continuar? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_status "INFO" "Cancelado pelo usuário"
    exit 0
fi

# Generate secure password for Grafana
GRAFANA_PASSWORD=$(openssl rand -base64 32)

echo ""
print_status "INFO" "Configurando Prometheus..."

# Update Prometheus config for the user's app
cat > prometheus/prometheus-railway.yml << EOF
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "/etc/prometheus/alerts/*.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets: []

scrape_configs:
  - job_name: 'whatsapp-agent'
    static_configs:
      - targets: ['$APP_URL']
    metrics_path: '/metrics'
    scheme: 'https'
    scrape_interval: 15s
    scrape_timeout: 10s
    honor_labels: true
    
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
    metrics_path: '/metrics'
    scrape_interval: 15s
EOF

print_status "SUCCESS" "Configuração do Prometheus atualizada"

# Configure Prometheus service
print_status "INFO" "Configurando serviço Prometheus..."

# Link to Prometheus project
railway link $PROMETHEUS_PROJECT

# Set environment variables for Prometheus
railway variables set PROMETHEUS_RETENTION_TIME=15d
railway variables set PORT=9090

# Deploy Prometheus with updated config
cp Dockerfile.prometheus Dockerfile
print_status "INFO" "Fazendo deploy do Prometheus..."
railway deploy --detach

rm -f Dockerfile

print_status "SUCCESS" "Prometheus configurado e deployed"

# Configure Grafana service
print_status "INFO" "Configurando serviço Grafana..."

# Link to Grafana project
railway link $GRAFANA_PROJECT

# Set environment variables for Grafana
railway variables set GF_SECURITY_ADMIN_PASSWORD="$GRAFANA_PASSWORD"
railway variables set GF_INSTALL_PLUGINS="grafana-piechart-panel"
railway variables set GF_SERVER_ROOT_URL="https://\${RAILWAY_PUBLIC_DOMAIN}"
railway variables set GF_SECURITY_ALLOW_EMBEDDING="true"
railway variables set GF_AUTH_ANONYMOUS_ENABLED="false"
railway variables set PORT=3000

# Deploy Grafana
cp Dockerfile.grafana Dockerfile
print_status "INFO" "Fazendo deploy do Grafana..."
railway deploy --detach

rm -f Dockerfile

print_status "SUCCESS" "Grafana configurado e deployed"

# Wait for services to be ready
print_status "INFO" "Aguardando serviços ficarem prontos (2-3 minutos)..."
echo "⏳ Isso pode levar alguns minutos..."

# Get service URLs
sleep 30  # Give time for deployment to start

print_status "INFO" "Obtendo URLs dos serviços..."

# Try to get URLs from Railway
railway link $PROMETHEUS_PROJECT
PROMETHEUS_URL=$(railway status --json 2>/dev/null | grep -o '"url":"[^"]*"' | cut -d'"' -f4 || echo "")
if [ -z "$PROMETHEUS_URL" ]; then
    PROMETHEUS_URL="https://$PROMETHEUS_PROJECT.railway.app"
fi

railway link $GRAFANA_PROJECT  
GRAFANA_URL=$(railway status --json 2>/dev/null | grep -o '"url":"[^"]*"' | cut -d'"' -f4 || echo "")
if [ -z "$GRAFANA_URL" ]; then
    GRAFANA_URL="https://$GRAFANA_PROJECT.railway.app"
fi

# Create deployment summary
cat > RAILWAY_CONFIG_SUMMARY.md << EOF
# Configuração Railway Concluída

## 🚀 Serviços Configurados

### Prometheus
- **URL**: $PROMETHEUS_URL
- **Projeto**: $PROMETHEUS_PROJECT
- **Retenção**: 15 dias
- **Target**: $APP_URL

### Grafana
- **URL**: $GRAFANA_URL
- **Projeto**: $GRAFANA_PROJECT
- **Usuário**: admin
- **Senha**: $GRAFANA_PASSWORD

## 📋 Próximos Passos

### 1. Aguardar Deploy (2-3 minutos)
Os serviços estão sendo deployed. Aguarde alguns minutos.

### 2. Acessar Grafana
1. Vá para: $GRAFANA_URL
2. Login: admin
3. Senha: $GRAFANA_PASSWORD

### 3. Importar Dashboard
1. No Grafana, vá em "+" → Import
2. Clique em "Upload JSON file"
3. Selecione o arquivo: grafana/whatsapp_agent_dashboard.json
4. Clique em "Import"

### 4. Verificar Prometheus
1. Vá para: $PROMETHEUS_URL
2. Clique em "Status" → "Targets"
3. Verifique se o target 'whatsapp-agent' está UP

### 5. Verificar Métricas
Acesse: https://$APP_URL/metrics
Deve mostrar métricas do Prometheus.

## 🔧 Se algo não funcionar

### Logs dos serviços:
\`\`\`bash
# Ver logs do Prometheus
railway link $PROMETHEUS_PROJECT
railway logs

# Ver logs do Grafana  
railway link $GRAFANA_PROJECT
railway logs
\`\`\`

### Verificar variáveis:
\`\`\`bash
railway variables
\`\`\`

Gerado em: $(date)
EOF

echo ""
echo "🎉 Configuração Concluída!"
echo "========================="
echo ""
echo -e "${GREEN}📊 Grafana:${NC} $GRAFANA_URL"
echo -e "${GREEN}📈 Prometheus:${NC} $PROMETHEUS_URL"
echo -e "${GREEN}🔑 Senha Grafana:${NC} $GRAFANA_PASSWORD"
echo ""
echo -e "${BLUE}📋 Detalhes salvos em:${NC} RAILWAY_CONFIG_SUMMARY.md"
echo ""
echo -e "${YELLOW}⏳ Aguarde 2-3 minutos para os serviços ficarem prontos${NC}"
echo ""
echo "Próximos passos:"
echo "1. Acesse o Grafana com admin/$GRAFANA_PASSWORD"
echo "2. Importe o dashboard: grafana/whatsapp_agent_dashboard.json" 
echo "3. Verifique se o Prometheus está coletando métricas"

print_status "SUCCESS" "Sistema de monitoramento configurado com sucesso!"
