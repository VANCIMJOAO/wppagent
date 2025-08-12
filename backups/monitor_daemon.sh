#!/bin/bash
# monitor_daemon.sh - Script para executar o monitor como daemon

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_PATH="$SCRIPT_DIR/venv/bin/python"
MONITOR_SCRIPT="$SCRIPT_DIR/monitor.py"
PID_FILE="$SCRIPT_DIR/logs/monitor.pid"
LOG_FILE="$SCRIPT_DIR/logs/monitor_daemon.log"

# Criar diretório de logs se não existir
mkdir -p "$SCRIPT_DIR/logs"

start_monitor() {
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        echo "⚠️  Monitor já está rodando (PID: $(cat "$PID_FILE"))"
        return 1
    fi
    
    echo "🚀 Iniciando monitor do sistema..."
    
    # Iniciar monitor em background
    nohup "$PYTHON_PATH" "$MONITOR_SCRIPT" --continuous --interval 300 --save-report > "$LOG_FILE" 2>&1 &
    
    # Salvar PID
    echo $! > "$PID_FILE"
    
    echo "✅ Monitor iniciado (PID: $!)"
    echo "📁 Logs em: $LOG_FILE"
}

stop_monitor() {
    if [ ! -f "$PID_FILE" ]; then
        echo "⚠️  Monitor não está rodando"
        return 1
    fi
    
    PID=$(cat "$PID_FILE")
    
    if kill -0 "$PID" 2>/dev/null; then
        echo "🛑 Parando monitor (PID: $PID)..."
        kill "$PID"
        
        # Aguardar até 10 segundos para parar graciosamente
        for i in {1..10}; do
            if ! kill -0 "$PID" 2>/dev/null; then
                break
            fi
            sleep 1
        done
        
        # Forçar parada se necessário
        if kill -0 "$PID" 2>/dev/null; then
            echo "⚠️  Forçando parada..."
            kill -9 "$PID"
        fi
        
        rm -f "$PID_FILE"
        echo "✅ Monitor parado"
    else
        echo "⚠️  Processo não encontrado, removendo PID file"
        rm -f "$PID_FILE"
    fi
}

status_monitor() {
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        PID=$(cat "$PID_FILE")
        echo "✅ Monitor rodando (PID: $PID)"
        
        # Mostrar informações do processo
        if command -v ps >/dev/null 2>&1; then
            echo "📊 Processo:"
            ps -p "$PID" -o pid,ppid,user,start,time,command 2>/dev/null || echo "   Informações não disponíveis"
        fi
        
        # Mostrar últimas linhas do log
        if [ -f "$LOG_FILE" ]; then
            echo "📝 Últimas 5 linhas do log:"
            tail -n 5 "$LOG_FILE"
        fi
        
        return 0
    else
        echo "❌ Monitor não está rodando"
        if [ -f "$PID_FILE" ]; then
            echo "   Removendo PID file órfão..."
            rm -f "$PID_FILE"
        fi
        return 1
    fi
}

restart_monitor() {
    echo "🔄 Reiniciando monitor..."
    stop_monitor
    sleep 2
    start_monitor
}

show_logs() {
    if [ -f "$LOG_FILE" ]; then
        echo "📝 Logs do monitor:"
        echo "=================="
        tail -n 50 "$LOG_FILE"
    else
        echo "❌ Arquivo de log não encontrado: $LOG_FILE"
    fi
}

check_health() {
    echo "🔍 Executando verificação única de saúde..."
    "$PYTHON_PATH" "$MONITOR_SCRIPT" --check-all --save-report
}

case "$1" in
    start)
        start_monitor
        ;;
    stop)
        stop_monitor
        ;;
    restart)
        restart_monitor
        ;;
    status)
        status_monitor
        ;;
    logs)
        show_logs
        ;;
    check)
        check_health
        ;;
    *)
        echo "🔧 Monitor do Sistema WhatsApp Agent"
        echo "=================================="
        echo "Uso: $0 {start|stop|restart|status|logs|check}"
        echo ""
        echo "Comandos:"
        echo "  start   - Iniciar monitor em background"
        echo "  stop    - Parar monitor"
        echo "  restart - Reiniciar monitor"
        echo "  status  - Ver status do monitor"
        echo "  logs    - Ver logs recentes"
        echo "  check   - Executar verificação única"
        echo ""
        echo "Arquivos:"
        echo "  PID:  $PID_FILE"
        echo "  Log:  $LOG_FILE"
        exit 1
        ;;
esac

exit 0
