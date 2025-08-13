#!/bin/bash

# Quick Railway Deployment Script
# Simple one-command deployment for Railway monitoring stack

set -e

echo "🚀 Railway Monitoring Quick Deploy"
echo "=================================="

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Installing..."
    npm install -g @railway/cli
fi

# Authenticate if needed
echo "🔐 Checking Railway authentication..."
if ! railway whoami &> /dev/null; then
    echo "Please login to Railway:"
    railway login
fi

# Get app URL
echo ""
read -p "📱 Enter your WhatsApp Agent Railway URL (e.g., your-app.railway.app): " APP_URL

if [ -z "$APP_URL" ]; then
    echo "❌ App URL is required"
    exit 1
fi

# Update Prometheus config
echo "🔧 Updating Prometheus configuration..."
sed -i "s/your-app.railway.app/$APP_URL/g" prometheus/prometheus-railway.yml

# Generate secure password
GRAFANA_PASSWORD=$(openssl rand -base64 32)
echo "🔑 Generated Grafana password: $GRAFANA_PASSWORD"

# Deploy Prometheus
echo "📊 Deploying Prometheus service..."
railway create whatsapp-monitoring-prometheus || echo "Project may already exist"
railway link whatsapp-monitoring-prometheus

# Set environment variables
railway variables set PROMETHEUS_RETENTION_TIME=15d
railway variables set PORT=9090

# Deploy using Dockerfile
cp Dockerfile.prometheus Dockerfile
railway deploy --detach
PROMETHEUS_URL=$(railway status --json | jq -r '.latestDeployment.url' 2>/dev/null || echo "Check Railway dashboard")

# Deploy Grafana in separate project
echo "📈 Deploying Grafana service..."
railway create whatsapp-monitoring-grafana || echo "Project may already exist"
railway link whatsapp-monitoring-grafana

# Set Grafana environment variables
railway variables set GF_SECURITY_ADMIN_PASSWORD="$GRAFANA_PASSWORD"
railway variables set GF_INSTALL_PLUGINS=grafana-piechart-panel
railway variables set PORT=3000

# Update Grafana datasource config with Prometheus URL
if [ "$PROMETHEUS_URL" != "Check Railway dashboard" ]; then
    sed -i "s|http://prometheus:9090|$PROMETHEUS_URL|g" grafana/datasources/prometheus.yml
fi

# Deploy Grafana
cp Dockerfile.grafana Dockerfile  
railway deploy --detach
GRAFANA_URL=$(railway status --json | jq -r '.latestDeployment.url' 2>/dev/null || echo "Check Railway dashboard")

# Create deployment summary
cat > RAILWAY_QUICK_DEPLOY_SUMMARY.md << EOF
# Railway Monitoring Quick Deploy Summary

## 🚀 Deployed Services

### Prometheus
- **URL**: $PROMETHEUS_URL
- **Project**: whatsapp-monitoring-prometheus

### Grafana  
- **URL**: $GRAFANA_URL
- **Username**: admin
- **Password**: $GRAFANA_PASSWORD
- **Project**: whatsapp-monitoring-grafana

## 📋 Next Steps

1. **Wait for deployment** (2-3 minutes)
2. **Access Grafana**: Visit $GRAFANA_URL
3. **Login**: Use admin / $GRAFANA_PASSWORD
4. **Import Dashboard**: Upload grafana/whatsapp_agent_dashboard.json
5. **Verify Metrics**: Check $APP_URL/metrics

## 🔧 Manual Steps Required

1. **Import Dashboard**: 
   - Go to Grafana → Dashboards → Import
   - Upload grafana/whatsapp_agent_dashboard.json

2. **Verify Datasource**:
   - Go to Configuration → Data Sources
   - Check Prometheus connection

## 📱 URLs
- **Application**: https://$APP_URL
- **Prometheus**: $PROMETHEUS_URL  
- **Grafana**: $GRAFANA_URL

Generated: $(date)
EOF

echo ""
echo "🎉 Railway Monitoring Stack Deployed!"
echo "===================================="
echo ""
echo "📊 Grafana: $GRAFANA_URL"
echo "📈 Prometheus: $PROMETHEUS_URL" 
echo "🔑 Password: $GRAFANA_PASSWORD"
echo ""
echo "📋 Summary saved to: RAILWAY_QUICK_DEPLOY_SUMMARY.md"
echo ""
echo "⏳ Wait 2-3 minutes for services to start, then access Grafana!"

# Cleanup
rm -f Dockerfile
