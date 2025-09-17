#!/bin/bash
# 🔍 SUPER DEBUG RAILWAY - Diagnóstico Completo
# Este script força debugging máximo para encontrar exatamente o que está acontecendo

set -e

echo "🔍 =============== SUPER DEBUG RAILWAY ==============="
echo "🕐 Iniciado em: $(date)"
echo "📊 Modo: Diagnóstico Completo Railway"
echo "=================================================="

# 1. INFORMAÇÕES DO SISTEMA RAILWAY
echo -e "\n🌐 === RAILWAY SYSTEM INFO ==="
echo "Railway CLI Version:"
railway --version 2>/dev/null || echo "❌ Railway CLI não encontrado"

echo -e "\n📡 Railway Project Info:"
timeout 10 railway status 2>/dev/null || echo "❌ Timeout ao obter status"

echo -e "\n🔑 Railway Environment Variables (primeiras 5):"
timeout 15 railway variables 2>/dev/null | head -5 || echo "❌ Timeout ao obter variáveis"

# 2. TESTE DE CONECTIVIDADE RAILWAY
echo -e "\n🌍 === RAILWAY CONNECTIVITY TEST ==="
echo "🔍 Testing Railway domain resolution:"
nslookup wppagent-production.up.railway.app 2>/dev/null || echo "❌ DNS lookup failed"

echo -e "\n🔍 Testing Railway ping:"
ping -c 3 wppagent-production.up.railway.app 2>/dev/null || echo "❌ Ping failed"

echo -e "\n🔍 Testing Railway HTTP connectivity:"
timeout 10 curl -I https://wppagent-production.up.railway.app/ 2>/dev/null || echo "❌ HTTP test failed"

# 3. TESTE DE ENDPOINTS ESPECÍFICOS
echo -e "\n🎯 === ENDPOINT TESTING ==="
ENDPOINTS=(
    "/ping"
    "/health"
    "/ready"
    "/alive"
    "/"
)

for endpoint in "${ENDPOINTS[@]}"; do
    echo "🔍 Testing $endpoint:"
    timeout 5 curl -s -w "Status: %{http_code}, Time: %{time_total}s\n" \
        "https://wppagent-production.up.railway.app$endpoint" 2>/dev/null || echo "❌ Failed"
done

# 4. LOGS RAILWAY COM MÚLTIPLAS TENTATIVAS
echo -e "\n📋 === RAILWAY LOGS ANALYSIS ==="
echo "🔍 Tentativa 1 - Logs recentes (timeout 10s):"
timeout 10 railway logs 2>/dev/null | tail -10 || echo "❌ Timeout nos logs - tentativa 1"

echo -e "\n🔍 Tentativa 2 - Logs com grep (timeout 15s):"
timeout 15 railway logs 2>/dev/null | grep -E "(ERROR|WARN|uvicorn|port|startup|failed)" | tail -5 || echo "❌ Nenhum log de erro encontrado"

echo -e "\n🔍 Tentativa 3 - Logs em JSON (timeout 10s):"
timeout 10 railway logs --json 2>/dev/null | head -3 || echo "❌ Logs JSON indisponíveis"

# 5. ANÁLISE DETALHADA DO DEPLOYMENT
echo -e "\n🚀 === DEPLOYMENT ANALYSIS ==="
echo "🔍 Checking if deployment is stuck:"
ps aux | grep railway | grep -v grep || echo "ℹ️ Nenhum processo railway local"

echo -e "\n🔍 Checking local Railway config:"
if [ -f ".railway/config.json" ]; then
    echo "✅ Railway config encontrado"
    cat .railway/config.json 2>/dev/null | jq . 2>/dev/null || echo "⚠️ Config não é JSON válido"
else
    echo "❌ Railway config não encontrado"
fi

# 6. TESTE LOCAL DE STARTUP
echo -e "\n🧪 === LOCAL STARTUP TEST ==="
echo "🔍 Testing railway_start.sh syntax:"
bash -n railway_start.sh && echo "✅ Sintaxe OK" || echo "❌ Erro de sintaxe"

echo -e "\n🔍 Testing environment simulation:"
export PORT=8000 RAILWAY_ENVIRONMENT=production
echo "PORT: $PORT"
echo "RAILWAY_ENVIRONMENT: $RAILWAY_ENVIRONMENT"

echo -e "\n🔍 Testing Python app import:"
timeout 10 python -c "
import sys
sys.path.insert(0, '.')
try:
    from app.main import app
    print('✅ App import successful')
    print(f'App type: {type(app)}')
except Exception as e:
    print(f'❌ App import failed: {e}')
" 2>/dev/null || echo "❌ Timeout no teste de import"

# 7. ANÁLISE DO DOCKERFILE
echo -e "\n🐳 === DOCKERFILE ANALYSIS ==="
echo "🔍 Dockerfile content (últimas 10 linhas):"
tail -10 Dockerfile 2>/dev/null || echo "❌ Dockerfile não encontrado"

echo -e "\n🔍 railway.toml config:"
cat railway.toml 2>/dev/null || echo "❌ railway.toml não encontrado"

# 8. NETWORK DIAGNOSTICS
echo -e "\n🌐 === NETWORK DIAGNOSTICS ==="
echo "🔍 Current network interfaces:"
ip addr show 2>/dev/null | grep -E "(inet|UP)" | head -5 || echo "❌ Network info indisponível"

echo -e "\n🔍 Open ports:"
ss -tlnp 2>/dev/null | grep -E "(8000|8080)" || echo "ℹ️ Nenhuma porta 8000/8080 aberta"

# 9. RAILWAY SERVICE STATUS
echo -e "\n⚡ === RAILWAY SERVICE STATUS ==="
echo "🔍 Attempting to get service info:"
timeout 10 railway service 2>/dev/null || echo "❌ Service info indisponível"

# 10. FORÇA REBUILD SE POSSÍVEL
echo -e "\n🔄 === FORCE ACTIONS ==="
echo "🔍 Attempting to force redeploy (non-interactive):"
echo "n" | timeout 15 railway redeploy 2>/dev/null || echo "❌ Redeploy cancelado/falhou"

# 11. FINAL SUMMARY
echo -e "\n📊 === SUMMARY ==="
echo "🕐 Debug concluído em: $(date)"
echo "🔍 Próximos passos recomendados:"
echo "   1. Verificar se o Railway está em manutenção"
echo "   2. Tentar um novo deploy manual: railway up"
echo "   3. Verificar limites da conta Railway"
echo "   4. Considerar restart do serviço via web interface"
echo "=================================================="