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
