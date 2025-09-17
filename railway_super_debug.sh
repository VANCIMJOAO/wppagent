#!/bin/bash
# 🔍 SUPER DEPURAÇÃO RAILWAY - Diagnóstico Completo
# Script para investigar todos os aspectos do servidor Railway

echo "🔥 RAILWAY SUPER DEBUG - $(date)"
echo "=============================================="

# Função para fazer requests com timeout e detalhes
test_endpoint() {
    local endpoint="$1"
    local description="$2"
    
    echo -e "\n🌐 TESTANDO: $description"
    echo "URL: https://wppagent-production.up.railway.app$endpoint"
    
    # Teste com curl verbose
    curl -v -w "\n📊 MÉTRICAS:\nStatus Code: %{http_code}\nTime Total: %{time_total}s\nTime Connect: %{time_connect}s\nTime NameLookup: %{time_namelookup}s\nSize Download: %{size_download} bytes\n" \
         -H "User-Agent: Railway-Debug/1.0" \
         -H "Accept: application/json" \
         --connect-timeout 10 \
         --max-time 30 \
         "https://wppagent-production.up.railway.app$endpoint" 2>&1 | head -50
    
    echo -e "\n" | tr '\n' '-' | head -c 50 && echo ""
}

# 1. TESTES DE CONECTIVIDADE BÁSICA
echo -e "\n🌐 1. TESTES DE CONECTIVIDADE BÁSICA"
echo "======================================"

echo "📡 DNS Resolution:"
nslookup wppagent-production.up.railway.app || echo "❌ DNS failed"

echo -e "\n🔌 TCP Connection Test:"
timeout 10 bash -c "</dev/tcp/wppagent-production.up.railway.app/443" && echo "✅ TCP 443 OK" || echo "❌ TCP 443 failed"

echo -e "\n🌍 Railway Edge Servers Test:"
curl -v --connect-timeout 5 --max-time 10 https://wppagent-production.up.railway.app/ 2>&1 | grep -E "(Connected to|Server:|HTTP|Location)" | head -10

# 2. TESTES DE ENDPOINTS ESPECÍFICOS
echo -e "\n🎯 2. TESTES DE ENDPOINTS ESPECÍFICOS"
echo "====================================="

test_endpoint "/" "Root endpoint"
test_endpoint "/ping" "Health check ping"
test_endpoint "/health" "Health endpoint"
test_endpoint "/docs" "API Documentation"
test_endpoint "/openapi.json" "OpenAPI spec"

# 3. ANÁLISE DE HEADERS E RESPOSTA
echo -e "\n📋 3. ANÁLISE DETALHADA DE HEADERS"
echo "=================================="

echo "🔍 Headers completos do /ping:"
curl -I -v --connect-timeout 10 --max-time 15 https://wppagent-production.up.railway.app/ping 2>&1

# 4. TESTE COM DIFERENTES USER AGENTS
echo -e "\n🤖 4. TESTE COM DIFERENTES USER AGENTS"
echo "======================================"

declare -a user_agents=(
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    "Railway-Debug/1.0"
    "Python/httpx"
    "curl/7.68.0"
)

for ua in "${user_agents[@]}"; do
    echo -e "\n🔍 User-Agent: $ua"
    curl -s -w "Status: %{http_code} | Time: %{time_total}s" \
         -H "User-Agent: $ua" \
         https://wppagent-production.up.railway.app/ping | head -1
done

# 5. TESTE DE DIFERENTES MÉTODOS HTTP
echo -e "\n📡 5. TESTE DE DIFERENTES MÉTODOS HTTP"
echo "====================================="

declare -a methods=("GET" "POST" "HEAD" "OPTIONS")

for method in "${methods[@]}"; do
    echo -e "\n🔍 Método: $method"
    curl -s -w "Status: %{http_code}" -X "$method" \
         https://wppagent-production.up.railway.app/ping | head -1
done

# 6. ANÁLISE DE TEMPO DE RESPOSTA
echo -e "\n⏱️ 6. ANÁLISE DE TEMPO DE RESPOSTA (10 tentativas)"
echo "================================================="

for i in {1..10}; do
    echo -n "Tentativa $i: "
    curl -s -w "%{http_code} - %{time_total}s" \
         --connect-timeout 5 --max-time 15 \
         https://wppagent-production.up.railway.app/ping | head -1
done

# 7. VERIFICAÇÃO DE CERTIFICADO SSL
echo -e "\n🔒 7. VERIFICAÇÃO DE CERTIFICADO SSL"
echo "==================================="

echo "📜 Informações do certificado:"
openssl s_client -connect wppagent-production.up.railway.app:443 -servername wppagent-production.up.railway.app </dev/null 2>/dev/null | openssl x509 -noout -dates -subject -issuer

# 8. TESTE COM HTTP/1.1 vs HTTP/2
echo -e "\n🌐 8. TESTE HTTP/1.1 vs HTTP/2"
echo "============================="

echo "🔍 HTTP/1.1:"
curl -s -w "Protocol: %{http_version} | Status: %{http_code}" \
     --http1.1 https://wppagent-production.up.railway.app/ping | head -1

echo -e "\n🔍 HTTP/2:"
curl -s -w "Protocol: %{http_version} | Status: %{http_code}" \
     --http2 https://wppagent-production.up.railway.app/ping | head -1

# 9. TESTE DE RATE LIMITING
echo -e "\n🚦 9. TESTE DE RATE LIMITING (5 requests rápidos)"
echo "=============================================="

for i in {1..5}; do
    echo -n "Request $i: "
    curl -s -w "%{http_code}" https://wppagent-production.up.railway.app/ping | head -1
    sleep 0.1
done

# 10. COMPARAÇÃO COM OUTRO SERVIÇO RAILWAY
echo -e "\n🔄 10. TESTE DE REFERÊNCIA (httpbin.org)"
echo "======================================="

echo "🌐 Testando httpbin.org para comparação:"
curl -s -w "Status: %{http_code} | Time: %{time_total}s" https://httpbin.org/status/200 | head -1

# 11. VERIFICAÇÃO DE LOGS DO RAILWAY (simulação)
echo -e "\n📋 11. RESUMO DE POSSÍVEIS PROBLEMAS"
echo "==================================="

echo "🔍 Possíveis causas do 502:"
echo "1. ❌ Aplicação não iniciou corretamente"
echo "2. ❌ Porta não está sendo ouvida corretamente" 
echo "3. ❌ Health check falhando"
echo "4. ❌ Timeout de inicialização"
echo "5. ❌ Erro de binding da aplicação"
echo "6. ❌ Problema de proxy reverso do Railway"

echo -e "\n✅ DEPURAÇÃO COMPLETA FINALIZADA"
echo "Verifique os resultados acima para identificar o problema!"