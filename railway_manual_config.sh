#!/bin/bash

# Configuração Manual para Railway - SEM CLI
# Para quando você quer configurar via interface web do Railway

echo "🌐 Configurador Manual para Railway (SEM CLI)"
echo "=============================================="
echo ""

# Get app URL
echo "📱 Informações necessárias:"
echo ""
read -p "1. URL da sua aplicação WhatsApp Agent (ex: minha-app.railway.app): " APP_URL

if [ -z "$APP_URL" ]; then
    echo "❌ URL da aplicação é obrigatória"
    exit 1
fi

# Clean up URL
APP_URL=$(echo "$APP_URL" | sed 's|https://||g' | sed 's|http://||g')

# Generate secure password
GRAFANA_PASSWORD=$(openssl rand -base64 32)

echo ""
echo "🔧 Configurando arquivos locais..."

# Update Prometheus config
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
    
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
    metrics_path: '/metrics'
    scrape_interval: 15s
EOF

echo "✅ Prometheus config atualizado"

# Create manual instructions
cat > RAILWAY_MANUAL_SETUP.md << EOF
# 📋 Configuração Manual do Railway

## 🎯 Configuração do Prometheus

### 1. No seu projeto Prometheus no Railway:

#### Variáveis de Ambiente:
\`\`\`
PROMETHEUS_RETENTION_TIME=15d
PORT=9090
\`\`\`

#### Deploy Settings:
- **Dockerfile**: Use o \`Dockerfile.prometheus\` deste repositório
- **Source**: Conecte ao seu repositório GitHub
- **Build Command**: (deixe vazio, usa o Dockerfile)

### 2. Upload dos arquivos de configuração:
- Certifique-se que a pasta \`prometheus/\` está no seu repositório
- O arquivo \`prometheus-railway.yml\` foi atualizado com sua URL: **$APP_URL**

---

## 📊 Configuração do Grafana  

### 1. No seu projeto Grafana no Railway:

#### Variáveis de Ambiente:
\`\`\`
GF_SECURITY_ADMIN_PASSWORD=$GRAFANA_PASSWORD
GF_INSTALL_PLUGINS=grafana-piechart-panel
GF_SERVER_ROOT_URL=https://\${RAILWAY_PUBLIC_DOMAIN}
GF_SECURITY_ALLOW_EMBEDDING=true
GF_AUTH_ANONYMOUS_ENABLED=false
PORT=3000
\`\`\`

#### Deploy Settings:
- **Dockerfile**: Use o \`Dockerfile.grafana\` deste repositório  
- **Source**: Conecte ao seu repositório GitHub
- **Build Command**: (deixe vazio, usa o Dockerfile)

### 2. Upload dos arquivos de configuração:
- Certifique-se que a pasta \`grafana/\` está no seu repositório
- Dashboard será importado automaticamente

---

## 🚀 Passo a Passo no Railway

### Para o Prometheus:
1. Acesse seu projeto Prometheus no Railway
2. Vá em **Variables** e adicione as variáveis acima
3. Vá em **Settings** → **Source** → conecte ao GitHub
4. Vá em **Settings** → **Deploy** → defina \`Dockerfile.prometheus\`
5. Clique em **Deploy**

### Para o Grafana:
1. Acesse seu projeto Grafana no Railway  
2. Vá em **Variables** e adicione as variáveis acima
3. Vá em **Settings** → **Source** → conecte ao GitHub
4. Vá em **Settings** → **Deploy** → defina \`Dockerfile.grafana\`
5. Clique em **Deploy**

---

## 📱 Credenciais e URLs

### Grafana:
- **Usuário**: admin
- **Senha**: \`$GRAFANA_PASSWORD\`
- **URL**: Será fornecida pelo Railway após o deploy

### Prometheus:
- **URL**: Será fornecida pelo Railway após o deploy

---

## 📊 Verificação Final

### 1. Aguarde o deploy (2-3 minutos)

### 2. Teste o Prometheus:
- Acesse a URL do Prometheus
- Vá em **Status** → **Targets**
- Verifique se o target 'whatsapp-agent' está **UP**

### 3. Teste o Grafana:
- Acesse a URL do Grafana
- Faça login com admin/senha
- O dashboard deve carregar automaticamente
- Se não, vá em **+** → **Import** → upload \`grafana/whatsapp_agent_dashboard.json\`

### 4. Teste as métricas:
- Acesse: https://$APP_URL/metrics
- Deve mostrar métricas do Prometheus

---

## 🔧 Troubleshooting

### Se o Prometheus não conseguir conectar na sua app:
1. Verifique se sua app tem o endpoint \`/metrics\` funcionando
2. Verifique se o \`prometheus_client\` está instalado na sua app
3. Verifique se a URL está correta em \`prometheus-railway.yml\`

### Se o Grafana não carregar o dashboard:
1. Verifique se os arquivos da pasta \`grafana/\` estão no repositório
2. Tente importar manualmente o dashboard
3. Verifique se o Prometheus está configurado como datasource

### Logs dos serviços:
- No Railway, vá no projeto → **Deployments** → clique no deploy → **Logs**

---

## 🎉 Próximos Passos

Depois que tudo estiver funcionando:
1. Salve as URLs e credenciais em local seguro
2. Configure alertas (opcional)
3. Customize o dashboard conforme necessário
4. Configure backup das configurações

**Senha do Grafana**: \`$GRAFANA_PASSWORD\`
**App monitorada**: https://$APP_URL

Gerado em: $(date)
EOF

# Create commit helper
cat > commit_railway_config.sh << EOF
#!/bin/bash
echo "🚀 Fazendo commit das configurações Railway..."
git add .
git commit -m "feat: Railway manual configuration

- Updated prometheus-railway.yml with app URL: $APP_URL  
- Added manual setup instructions
- Generated secure Grafana password
- Ready for Railway deployment via web interface"
git push origin main
echo "✅ Configurações enviadas para o GitHub!"
EOF

chmod +x commit_railway_config.sh

echo ""
echo "🎉 Configuração Manual Preparada!"
echo "================================="
echo ""
echo "📋 Instruções detalhadas: RAILWAY_MANUAL_SETUP.md"
echo "🔑 Senha do Grafana: $GRAFANA_PASSWORD"
echo ""
echo "📤 Para enviar as configurações para o GitHub:"
echo "./commit_railway_config.sh"
echo ""
echo "🌐 Próximos passos:"
echo "1. Execute: ./commit_railway_config.sh"
echo "2. Abra o Railway no navegador"
echo "3. Configure as variáveis conforme RAILWAY_MANUAL_SETUP.md"
echo "4. Faça deploy dos serviços"
echo ""
echo "✅ Configuração local concluída!"
