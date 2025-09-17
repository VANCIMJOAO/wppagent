#!/bin/bash
# 🔍 SIMULAÇÃO LOCAL DO RAILWAY - Diagnóstico do Container
echo "🚀 SIMULAÇÃO LOCAL DO RAILWAY ENVIRONMENT"
echo "========================================"

# Simular variáveis do Railway
export PORT=8000
export RAILWAY_ENVIRONMENT=production
export RAILWAY_SERVICE_NAME=wppagent-production
export RAILWAY_PROJECT_NAME=wppagent
export RAILWAY_FAST_START=true

echo "📋 Variáveis simuladas do Railway:"
echo "PORT: $PORT"
echo "RAILWAY_ENVIRONMENT: $RAILWAY_ENVIRONMENT"
echo "RAILWAY_SERVICE_NAME: $RAILWAY_SERVICE_NAME"

echo -e "\n🔍 1. TESTE DE IMPORTAÇÃO DA APLICAÇÃO"
echo "====================================="

echo "🐍 Testando importação do app.main..."
python -c "
import sys
print('Python path:', sys.path[:3])
try:
    from app.main import app
    print('✅ app.main importado com sucesso')
    print('App type:', type(app))
    print('App routes:', len(app.routes) if hasattr(app, 'routes') else 'N/A')
except Exception as e:
    print('❌ Erro na importação:', e)
    import traceback
    traceback.print_exc()
"

echo -e "\n🔍 2. TESTE DE INICIALIZAÇÃO UVICORN"
echo "==================================="

echo "🚀 Testando uvicorn import e configuração..."
python -c "
try:
    import uvicorn
    print('✅ uvicorn importado')
    print('uvicorn version:', uvicorn.__version__)
    
    # Teste configuração
    config = uvicorn.Config(
        'app.main:app',
        host='0.0.0.0',
        port=8000,
        log_level='info'
    )
    print('✅ Configuração uvicorn OK')
    print('Config:', config)
except Exception as e:
    print('❌ Erro uvicorn:', e)
    import traceback
    traceback.print_exc()
"

echo -e "\n🔍 3. TESTE DE PORTA E BINDING"
echo "============================="

echo "🔌 Testando binding na porta $PORT..."
python -c "
import socket
import time

port = int('$PORT')
try:
    # Teste de binding
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('0.0.0.0', port))
    s.listen(1)
    print(f'✅ Porta {port} disponível para binding')
    
    # Teste de conexão
    s.settimeout(1)
    print(f'✅ Socket criado e ouvindo na porta {port}')
    s.close()
    
except Exception as e:
    print(f'❌ Erro de binding na porta {port}:', e)
"

echo -e "\n🔍 4. TESTE DE DEPENDENCIES E IMPORTS"
echo "====================================="

echo "📦 Verificando dependências críticas..."
python -c "
critical_imports = [
    'fastapi', 'uvicorn', 'sqlalchemy', 'redis', 
    'httpx', 'pydantic', 'jwt', 'bcrypt'
]

for pkg in critical_imports:
    try:
        __import__(pkg)
        print(f'✅ {pkg}')
    except ImportError as e:
        print(f'❌ {pkg}: {e}')
"

echo -e "\n🔍 5. TESTE DE STARTUP RÁPIDO (FastAPI)"
echo "====================================="

echo "⚡ Iniciando FastAPI brevemente para testar..."
timeout 10 python -c "
import asyncio
from app.main import app
import uvicorn

async def quick_test():
    print('🚀 Iniciando servidor de teste...')
    config = uvicorn.Config(
        app, 
        host='0.0.0.0', 
        port=8000,
        log_level='critical'  # Silencioso
    )
    server = uvicorn.Server(config)
    
    # Teste de startup sem rodar
    try:
        await server.startup()
        print('✅ FastAPI startup OK')
        await server.shutdown()
        print('✅ FastAPI shutdown OK')
    except Exception as e:
        print(f'❌ Erro no startup: {e}')
        import traceback
        traceback.print_exc()

asyncio.run(quick_test())
" 2>&1 | head -20

echo -e "\n🔍 6. VERIFICAÇÃO DE LOGS E PROCESSOS"
echo "===================================="

echo "🔍 Verificando se há uvicorn rodando..."
ps aux | grep uvicorn || echo "Nenhum processo uvicorn encontrado"

echo -e "\n🔍 Verificando portas em uso..."
netstat -tlnp 2>/dev/null | grep :8000 || echo "Porta 8000 livre"

echo -e "\n📋 RESUMO DO DIAGNÓSTICO LOCAL"
echo "=========================="
echo "Se todos os testes acima passaram, o problema está específico do Railway."
echo "Se algum falhou, encontramos a causa do 502!"