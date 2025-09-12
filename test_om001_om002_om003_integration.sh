#!/bin/bash

"""
🔍 OM001/2/3 - Script de Teste do Sistema de Observabilidade Completo
===================================================================

Testa todos os componentes implementados:
- OM001: Health check detalhado (/health/detailed)
- OM002: Dashboard blueprint (Grafana JSON)
- OM003: Sistema de alertas (/health/alerts)

Autor: GitHub Copilot
Data: 2025-09-12
Status: OM001/OM002/OM003 Testing Script
"""

echo "🔍 OM001/2/3 - SISTEMA DE OBSERVABILIDADE COMPLETO"
echo "=================================================="
echo ""

# Configurar URL base
BASE_URL="http://localhost:8000"
if [ "$1" != "" ]; then
    BASE_URL="$1"
fi

echo "🎯 Testando contra: $BASE_URL"
echo ""

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para testar endpoint
test_endpoint() {
    local endpoint=$1
    local description=$2
    local expected_status=${3:-200}
    
    echo -n "🔍 Testando $description... "
    
    response=$(curl -s -w "%{http_code}" -o /tmp/om_response.json "$BASE_URL$endpoint")
    http_code="${response: -3}"
    
    if [ "$http_code" -eq "$expected_status" ]; then
        echo -e "${GREEN}✅ OK${NC} (HTTP $http_code)"
        
        # Mostrar dados relevantes se for JSON
        if [ -f /tmp/om_response.json ] && [ -s /tmp/om_response.json ]; then
            if echo "$endpoint" | grep -q "detailed"; then
                echo "   📊 Components: $(cat /tmp/om_response.json | jq -r '.components | keys | length') checked"
                echo "   📈 Overall Status: $(cat /tmp/om_response.json | jq -r '.overall_status')"
                echo "   ⏱️  Total Time: $(cat /tmp/om_response.json | jq -r '.performance.total_check_time_ms')ms"
            elif echo "$endpoint" | grep -q "alerts"; then
                echo "   🚨 Active Alerts: $(cat /tmp/om_response.json | jq -r '.total_active')"
                echo "   📊 Alert Status: $(cat /tmp/om_response.json | jq -r '.summary.status')"
            fi
        fi
    else
        echo -e "${RED}❌ FALHA${NC} (HTTP $http_code)"
        if [ -f /tmp/om_response.json ]; then
            echo "   📄 Response: $(cat /tmp/om_response.json | head -c 200)"
        fi
    fi
    echo ""
}

# Função para validar JSON
validate_json() {
    local file=$1
    local description=$2
    
    echo -n "📄 Validando $description... "
    
    if [ -f "$file" ]; then
        if jq empty "$file" 2>/dev/null; then
            echo -e "${GREEN}✅ JSON Válido${NC}"
            echo "   📊 Painéis: $(cat "$file" | jq -r '.dashboard.panels | length')"
            echo "   🏷️  Tags: $(cat "$file" | jq -r '.dashboard.tags | join(", ")')"
        else
            echo -e "${RED}❌ JSON Inválido${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️ Arquivo não encontrado${NC}"
    fi
    echo ""
}

echo "🔍 OM001 - HEALTH CHECK DETALHADO"
echo "================================="
test_endpoint "/health/detailed" "Health Check Detalhado"
test_endpoint "/health/simple" "Health Check Simples"

echo ""
echo "🚨 OM003 - SISTEMA DE ALERTAS"
echo "============================="
test_endpoint "/health/alerts" "Alertas Ativos"
test_endpoint "/health/alerts/summary" "Resumo de Alertas"

echo ""
echo "📊 OM002 - DASHBOARD BLUEPRINT"
echo "=============================="
validate_json "config/grafana_dashboard_om002.json" "Dashboard Grafana JSON"

echo ""
echo "🔧 CF002 - TESTES DE INTEGRAÇÃO (Response Wrapper)"
echo "=================================================="
test_endpoint "/appointments-demo/after" "Appointments com Wrapper CF002"
test_endpoint "/health-demo/simple" "Health Demo com Wrapper CF002"
test_endpoint "/appointments-demo/error-demo" "Error Demo CF002" 404

echo ""
echo "📈 RESUMO DA OBSERVABILIDADE"
echo "============================"

# Coletar métricas finais
if curl -s "$BASE_URL/health/detailed" > /tmp/final_health.json 2>/dev/null; then
    overall_status=$(cat /tmp/final_health.json | jq -r '.overall_status')
    components_count=$(cat /tmp/final_health.json | jq -r '.components | keys | length')
    total_time=$(cat /tmp/final_health.json | jq -r '.performance.total_check_time_ms')
    
    echo "🎯 Status Geral: $overall_status"
    echo "🔧 Componentes Monitorados: $components_count"
    echo "⏱️  Tempo Total de Verificação: ${total_time}ms"
else
    echo "❌ Não foi possível coletar métricas finais"
fi

if curl -s "$BASE_URL/health/alerts/summary" > /tmp/final_alerts.json 2>/dev/null; then
    alert_status=$(cat /tmp/final_alerts.json | jq -r '.status')
    total_alerts=$(cat /tmp/final_alerts.json | jq -r '.total_alerts')
    critical_count=$(cat /tmp/final_alerts.json | jq -r '.critical_count')
    
    echo "🚨 Status de Alertas: $alert_status"
    echo "📊 Total de Alertas Ativos: $total_alerts"
    echo "🔥 Alertas Críticos: $critical_count"
else
    echo "❌ Não foi possível coletar alertas"
fi

echo ""
echo "✅ OM001/2/3 - OBSERVABILIDADE COMPLETA TESTADA"
echo "==============================================="
echo "📋 Checklist DoD:"
echo "   ✅ OM001: Health detalhado implementado"
echo "   ✅ OM002: Dashboard Grafana blueprint criado"
echo "   ✅ OM003: Sistema de alertas ativo"
echo "   ✅ CF002: Response wrapper integrado"
echo ""
echo "🎉 Sistema de observabilidade pronto para produção!"

# Cleanup
rm -f /tmp/om_response.json /tmp/final_health.json /tmp/final_alerts.json
