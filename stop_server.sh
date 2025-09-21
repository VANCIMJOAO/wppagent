#!/bin/bash

# Script para parar o servidor WhatsApp Agent

echo "🛑 Parando WhatsApp Agent Server..."

# Ler PID do arquivo se existir
if [ -f "server.pid" ]; then
    SERVER_PID=$(cat server.pid)
    echo "📋 PID encontrado: $SERVER_PID"
    
    # Verificar se o processo ainda está rodando
    if ps -p $SERVER_PID > /dev/null; then
        echo "🔍 Processo encontrado, parando..."
        kill $SERVER_PID
        
        # Aguardar o processo parar
        sleep 2
        
        # Verificar se parou
        if ps -p $SERVER_PID > /dev/null; then
            echo "⚠️  Processo não parou, forçando..."
            kill -9 $SERVER_PID
            sleep 1
        fi
        
        echo "✅ Servidor parado com sucesso!"
    else
        echo "⚠️  Processo com PID $SERVER_PID não encontrado"
    fi
    
    # Remover arquivo PID
    rm -f server.pid
else
    echo "⚠️  Arquivo server.pid não encontrado"
fi

# Parar todos os processos uvicorn como fallback
echo "🧹 Limpando processos uvicorn restantes..."
pkill -f uvicorn 2>/dev/null || true

echo "✅ Limpeza concluída!"
