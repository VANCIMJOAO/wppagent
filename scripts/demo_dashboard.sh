#!/bin/bash

# 🎯 Demo do Sistema de Monitoramento Visual
# Este script demonstra como acessar e usar o dashboard visual

echo "🎯 SISTEMA DE MONITORAMENTO VISUAL - DASHBOARD"
echo "==============================================="
echo ""

# Verificar se o servidor está rodando
echo "🔍 Verificando se o servidor está rodando..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Servidor WhatsApp Agent rodando em http://localhost:8000"
else
    echo "❌ Servidor não está rodando. Execute: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
    exit 1
fi

echo ""
echo "📊 DASHBOARD VISUAL DISPONÍVEL EM:"
echo "=================================="
echo "🌐 URL Principal: http://localhost:8000/dashboard"
echo "🌐 URL Alternativa: http://localhost:8000/"
echo ""

echo "💡 RECURSOS DO DASHBOARD VISUAL:"
echo "==============================="
echo "• ⚡ Monitoramento em tempo real (atualização a cada 30s)"
echo "• 📈 Gráficos interativos com Chart.js"
echo "• 🎯 Status de saúde dos serviços"
echo "• 📊 Métricas de performance"
echo "• 🔄 Circuit breakers status"
echo "• 📱 Design responsivo"
echo "• 🎨 Interface moderna e intuitiva"
echo ""

echo "🛠️ ENDPOINTS DA API DISPONÍVEIS:"
echo "==============================="
echo "• GET /health - Status geral do sistema"
echo "• GET /metrics - Métricas completas"
echo "• GET /business-metrics - Métricas de negócio"
echo "• GET /performance - Métricas de performance"
echo "• GET /alerts - Alertas ativos"
echo ""

echo "🖥️ TESTE RÁPIDO DOS ENDPOINTS:"
echo "============================="

echo "🟢 Health Check:"
curl -s http://localhost:8000/health | jq -r '"Status: " + .status + " | Service: " + .service'

echo ""
echo "📊 Métricas do Sistema:"
curl -s http://localhost:8000/metrics | jq -r '.system | "Uptime: " + .uptime + " | Version: " + .version'

echo ""
echo "💼 Métricas de Negócio:"
curl -s http://localhost:8000/business-metrics 2>/dev/null | jq -r '.summary.period // "Dados ainda sendo coletados..."'

echo ""
echo "⚡ Performance:"
curl -s http://localhost:8000/performance 2>/dev/null | jq -r '.memory.usage_mb // "Dados sendo coletados..."' | head -1

echo ""
echo "🚨 Alertas:"
curl -s http://localhost:8000/alerts 2>/dev/null | jq -r 'if .active_alerts then (.active_alerts | length | tostring + " alertas ativos") else "Nenhum alerta ativo" end'

echo ""
echo "🎉 COMO USAR O DASHBOARD:"
echo "======================="
echo "1. 🌐 Abra seu navegador em: http://localhost:8000/dashboard"
echo "2. 👀 Observe os cards de status na parte superior"
echo "3. 📈 Veja os gráficos de métricas em tempo real"
echo "4. 🔄 O dashboard se atualiza automaticamente a cada 30 segundos"
echo "5. 📱 Funciona em desktop, tablet e mobile"
echo ""

echo "📋 DASHBOARD ALTERNATIVO (TERMINAL):"
echo "=================================="
echo "Para usar o dashboard no terminal, execute:"
echo "$ ./scripts/dashboard.sh"
echo ""

echo "✅ Sistema de Monitoramento Visual configurado e funcionando!"
echo "🎯 Acesse: http://localhost:8000/dashboard"
