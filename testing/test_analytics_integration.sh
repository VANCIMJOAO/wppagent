#!/bin/bash

# Script para testar integração Analytics API
echo "🔍 Testando Integração API Analytics..."

# Definir URLs
BACKEND_URL="http://localhost:8000"
FRONTEND_URL="http://localhost:3000"

echo ""
echo "=== 1. Testando Backend FastAPI ==="

# Testar endpoint dashboard-summary do backend
echo "📊 Testando $BACKEND_URL/api/analytics/dashboard-summary"
BACKEND_RESPONSE=$(curl -s -w "HTTP_CODE:%{http_code}" "$BACKEND_URL/api/analytics/dashboard-summary?days=7" 2>/dev/null)

if echo "$BACKEND_RESPONSE" | grep -q "HTTP_CODE:200"; then
    echo "✅ Backend API responde corretamente"
    echo "📝 Dados: $(echo "$BACKEND_RESPONSE" | sed 's/HTTP_CODE:200//')"
else
    echo "❌ Backend API não está respondendo ou retornou erro"
    echo "🔧 Código HTTP: $(echo "$BACKEND_RESPONSE" | grep -o 'HTTP_CODE:[0-9]*' || echo 'Sem resposta')"
fi

echo ""
echo "=== 2. Testando Frontend Next.js ==="

# Testar endpoint analytics/overview do frontend
echo "🌐 Testando $FRONTEND_URL/api/analytics/overview"
FRONTEND_RESPONSE=$(curl -s -w "HTTP_CODE:%{http_code}" "$FRONTEND_URL/api/analytics/overview?days=7" 2>/dev/null)

if echo "$FRONTEND_RESPONSE" | grep -q "HTTP_CODE:200"; then
    echo "✅ Frontend API responde corretamente"
    
    # Verificar se está usando backend ou mock
    if echo "$FRONTEND_RESPONSE" | grep -q '"source":"backend"'; then
        echo "🔗 Integração REAL com backend ativa"
    elif echo "$FRONTEND_RESPONSE" | grep -q '"source":"mock"'; then
        echo "📋 Usando dados simulados (backend indisponível)"
    else
        echo "⚠️ Fonte dos dados não identificada"
    fi
else
    echo "❌ Frontend API não está respondendo"
    echo "🔧 Código HTTP: $(echo "$FRONTEND_RESPONSE" | grep -o 'HTTP_CODE:[0-9]*' || echo 'Sem resposta')"
fi

echo ""
echo "=== 3. Testando Hook useAnalytics (simulação) ==="

# Simular chamada do hook useAnalytics
echo "🎯 Simulando chamada: fetch('/api/analytics/overview?start_date=2025-08-10&end_date=2025-09-09')"

HOOK_RESPONSE=$(curl -s -w "HTTP_CODE:%{http_code}" "$FRONTEND_URL/api/analytics/overview?start_date=2025-08-10&end_date=2025-09-09" 2>/dev/null)

if echo "$HOOK_RESPONSE" | grep -q "HTTP_CODE:200"; then
    echo "✅ Hook useAnalytics funcionaria corretamente"
    
    # Verificar estrutura da resposta
    if echo "$HOOK_RESPONSE" | grep -q '"conversationsOverTime"'; then
        echo "📈 Estrutura conversationsOverTime: OK"
    fi
    
    if echo "$HOOK_RESPONSE" | grep -q '"funnelData"'; then
        echo "📊 Estrutura funnelData: OK"
    fi
    
    if echo "$HOOK_RESPONSE" | grep -q '"totalConversations"'; then
        echo "🔢 Métricas totais: OK"
    fi
else
    echo "❌ Hook useAnalytics teria problemas"
fi

echo ""
echo "=== 4. Resumo da Integração ==="

# Verificar se backend está rodando
if pgrep -f "uvicorn.*main:app" > /dev/null; then
    echo "✅ Backend FastAPI está rodando"
else
    echo "❌ Backend FastAPI NÃO está rodando"
    echo "   💡 Execute: uvicorn app.main:app --reload"
fi

# Verificar se frontend está rodando  
if pgrep -f "next" > /dev/null; then
    echo "✅ Frontend Next.js está rodando"
else
    echo "❌ Frontend Next.js NÃO está rodando"
    echo "   💡 Execute: npm run dev"
fi

echo ""
echo "=== 5. Status Final ==="

if echo "$BACKEND_RESPONSE" | grep -q "HTTP_CODE:200" && echo "$FRONTEND_RESPONSE" | grep -q "HTTP_CODE:200"; then
    if echo "$FRONTEND_RESPONSE" | grep -q '"source":"backend"'; then
        echo "🎉 SUCESSO: Integração completa funcionando!"
        echo "   🔗 Frontend conectado ao backend real"
    else
        echo "⚠️  PARCIAL: APIs funcionam, mas usando dados simulados"
        echo "   🔧 Backend disponível mas frontend usando fallback"
    fi
else
    echo "❌ PROBLEMA: Integração não está funcionando"
    echo "   🔧 Verificar logs e configurações"
fi

echo ""
echo "📋 Para mais detalhes, verifique os logs dos serviços"
