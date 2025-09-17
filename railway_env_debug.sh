#!/bin/bash
# 🔍 RAILWAY ENVIRONMENT DEBUG - Análise das variáveis de ambiente

echo "🔍 RAILWAY ENVIRONMENT ANALYSIS"
echo "=============================="

echo "🌍 Environment Variables que o Railway pode estar usando:"
echo "PORT: ${PORT:-'NOT_SET'}"
echo "HOST: ${HOST:-'NOT_SET'}"  
echo "RAILWAY_ENVIRONMENT: ${RAILWAY_ENVIRONMENT:-'NOT_SET'}"
echo "RAILWAY_SERVICE_NAME: ${RAILWAY_SERVICE_NAME:-'NOT_SET'}"
echo "RAILWAY_PROJECT_NAME: ${RAILWAY_PROJECT_NAME:-'NOT_SET'}"
echo "RAILWAY_REPLICA_ID: ${RAILWAY_REPLICA_ID:-'NOT_SET'}"
echo "RAILWAY_DEPLOYMENT_ID: ${RAILWAY_DEPLOYMENT_ID:-'NOT_SET'}"
echo "RAILWAY_PUBLIC_DOMAIN: ${RAILWAY_PUBLIC_DOMAIN:-'NOT_SET'}"
echo "RAILWAY_PRIVATE_DOMAIN: ${RAILWAY_PRIVATE_DOMAIN:-'NOT_SET'}"

echo -e "\n🔍 Testando com diferentes PORTs que Railway pode usar:"

# Test common Railway ports
for port in 8000 3000 5000 8080 80; do
    echo -n "Testing port $port: "
    
    python -c "
import socket
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1)
    s.bind(('0.0.0.0', $port))
    s.close()
    print('✅ Available')
except Exception as e:
    print(f'❌ {e}')
"
done

echo -e "\n🔍 Railway pode estar esperando resposta em endpoints específicos:"

# Test if Railway expects specific endpoints
endpoints=("/health" "/ping" "/" "/status" "/ready" "/alive")

echo "🧪 Simulando requests internos do Railway para health checks:"

for endpoint in "${endpoints[@]}"; do
    echo "Testing internal request to $endpoint..."
    
    # Simulate Railway internal health check
    timeout 5 python -c "
import httpx
import asyncio

async def test_endpoint():
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get('http://localhost:8000$endpoint')
            print(f'✅ $endpoint: {response.status_code}')
            if response.status_code == 200:
                print(f'   Response: {response.text[:100]}...')
    except Exception as e:
        print(f'❌ $endpoint: {e}')

asyncio.run(test_endpoint())
" 2>/dev/null || echo "❌ $endpoint: Connection failed"
done

echo -e "\n🔍 POSSÍVEIS PROBLEMAS DO RAILWAY:"

echo "1. 🔌 Railway pode estar fazendo proxy para porta errada"
echo "2. ⏰ Railway health check timeout muito baixo"
echo "3. 🌐 Railway proxy não conseguindo conectar no container"
echo "4. 📊 Railway esperando resposta em formato específico"
echo "5. 🐳 Container pode estar crashando após startup"
echo "6. 🔧 Railway PORT env var não chegando corretamente"

echo -e "\n🔍 Vamos verificar se o Railway está tentando HTTP internamente:"

echo "Testing if Railway internal proxy works..."
curl -v --connect-timeout 5 --max-time 10 http://localhost:8000/ping 2>&1 | head -5 || echo "Local connection failed"

echo -e "\n✅ RAILWAY DEBUG COMPLETO"
echo "Ver logs acima para identificar o problema específico!"