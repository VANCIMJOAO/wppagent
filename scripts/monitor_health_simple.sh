#!/bin/bash
# Script de monitoramento de saúde

echo "🔍 Verificando saúde do sistema..."

# Verificar se o servidor está rodando
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Servidor principal: OK"
else
    echo "❌ Servidor principal: FALHA"
    exit 1
fi

# Verificar métricas
if curl -s http://localhost:8000/production/system/status > /dev/null; then
    echo "✅ Sistema de monitoramento: OK"
else
    echo "⚠️ Sistema de monitoramento: FALHA"
fi

# Verificar logs
if [ -f "logs/app.log" ]; then
    echo "✅ Sistema de logs: OK"
    echo "📊 Últimas 3 linhas do log:"
    tail -n 3 logs/app.log
else
    echo "⚠️ Sistema de logs: Arquivo não encontrado"
fi

echo "🔍 Verificação de saúde concluída"
