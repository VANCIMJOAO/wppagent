#!/bin/bash

# Script para verificar o status do servidor WhatsApp Agent

echo "🔍 Verificando status do WhatsApp Agent Server..."

# Verificar se há arquivo PID
if [ -f "server.pid" ]; then
    SERVER_PID=$(cat server.pid)
    echo "📋 PID do servidor: $SERVER_PID"
    
    # Verificar se o processo está rodando
    if ps -p $SERVER_PID > /dev/null; then
        echo "✅ Servidor está rodando (PID: $SERVER_PID)"
        
        # Testar conectividade
        echo "🔍 Testando conectividade..."
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            echo "✅ Servidor respondendo corretamente!"
            
            # Mostrar informações básicas
            echo ""
            echo "📊 Informações do servidor:"
            echo "🌐 URL: http://localhost:8000"
            echo "📱 Webhook: http://localhost:8000/webhook"
            echo "📚 Documentação: http://localhost:8000/docs"
            echo "🔧 OpenAPI: http://localhost:8000/openapi.json"
            
            # Mostrar uso de memória
            MEMORY=$(ps -p $SERVER_PID -o rss= | awk '{print $1/1024 " MB"}')
            echo "💾 Uso de memória: $MEMORY"
            
        else
            echo "⚠️  Servidor rodando mas não está respondendo"
        fi
    else
        echo "❌ Servidor não está rodando (PID $SERVER_PID não encontrado)"
        echo "🧹 Removendo arquivo PID obsoleto..."
        rm -f server.pid
    fi
else
    echo "⚠️  Arquivo server.pid não encontrado"
    
    # Verificar se há processos uvicorn rodando
    UVICORN_PIDS=$(pgrep -f uvicorn)
    if [ -n "$UVICORN_PIDS" ]; then
        echo "🔍 Encontrados processos uvicorn: $UVICORN_PIDS"
        echo "⚠️  Servidor pode estar rodando sem controle de PID"
    else
        echo "❌ Nenhum processo uvicorn encontrado"
    fi
fi

# Verificar portas em uso
echo ""
echo "🔍 Verificando portas em uso:"
netstat -tlnp | grep :8000 || echo "   Porta 8000 não está em uso"

# Verificar logs recentes
echo ""
echo "📝 Logs recentes:"
if [ -d "logs" ]; then
    LATEST_LOG=$(ls -t logs/server_*.log 2>/dev/null | head -1)
    if [ -n "$LATEST_LOG" ]; then
        echo "   Último log: $LATEST_LOG"
        echo "   Últimas 5 linhas:"
        tail -5 "$LATEST_LOG" | sed 's/^/   /'
    else
        echo "   Nenhum log encontrado"
    fi
else
    echo "   Diretório de logs não encontrado"
fi
