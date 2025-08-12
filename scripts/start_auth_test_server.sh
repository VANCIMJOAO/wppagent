#!/bin/bash

echo "🚀 Iniciando servidor de teste de autenticação na porta 8001..."

cd /home/vancim/whats_agent

# Verificar se Redis está rodando
if ! redis-cli ping > /dev/null 2>&1; then
    echo "❌ Redis não está rodando. Iniciando..."
    redis-server --daemonize yes
fi

# Iniciar servidor na porta 8001
nohup uvicorn test_auth_server:app --host 0.0.0.0 --port 8001 > auth_server_8001.log 2>&1 &
SERVER_PID=$!

echo "📝 Servidor iniciado com PID: $SERVER_PID"
echo "⏳ Aguardando inicialização..."
sleep 5

# Testar se está funcionando
if curl -s http://localhost:8001/health > /dev/null; then
    echo "✅ Servidor funcionando em http://localhost:8001"
    echo "📖 Documentação: http://localhost:8001/docs" 
    echo "🔗 URLs de teste:"
    echo "   • Health: http://localhost:8001/health"
    echo "   • Login: POST http://localhost:8001/auth/login"
    echo "   • 2FA Setup: POST http://localhost:8001/auth/2fa/setup"
    echo "   • Secrets: GET http://localhost:8001/secrets/list"
else
    echo "❌ Falha ao iniciar servidor"
    cat auth_server_8001.log
fi
