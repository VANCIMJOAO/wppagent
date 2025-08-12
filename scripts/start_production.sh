#!/bin/bash
# Script de inicialização para produção

echo "🚀 Iniciando WhatsApp Agent em modo produção..."

# Verificar se a porta está disponível
PORT=8000
if lsof -i :$PORT > /dev/null 2>&1; then
    echo "⚠️  Porta $PORT está em uso. Tentando parar processo existente..."
    PID=$(lsof -t -i :$PORT)
    if [ ! -z "$PID" ]; then
        kill $PID
        sleep 3
        if lsof -i :$PORT > /dev/null 2>&1; then
            echo "❌ Não foi possível liberar a porta $PORT"
            echo "💡 Execute: kill $(lsof -t -i :$PORT)"
            exit 1
        fi
    fi
fi

# Verificar se todos os sistemas estão prontos
python3 -c "
from app.services.production_logger import setup_production_logging
from app.services.business_metrics import metrics_collector
from app.services.automated_alerts import alert_manager
from app.services.performance_monitor import performance_monitor
from app.services.backup_system import backup_manager

print('✅ Todos os sistemas de produção carregados com sucesso!')
"

if [ $? -eq 0 ]; then
    echo "✅ Verificação dos sistemas concluída"
    echo "🌐 Iniciando servidor na porta $PORT..."
    echo "📊 Dashboard: http://localhost:$PORT/production/system/status"
    echo "📈 Métricas: http://localhost:$PORT/production/metrics/business"
    echo ""
    uvicorn app.main:app --host 0.0.0.0 --port $PORT --log-level info
else
    echo "❌ Falha na verificação dos sistemas"
    exit 1
fi
