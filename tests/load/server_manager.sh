#!/bin/bash

# Script para gerenciar servidor e testes independentemente
# TRILHA 2 FASE 2.2 - Load Testing Solution

SERVER_PID_FILE="/tmp/whatsapp_agent_server.pid"
VENV_PATH="/home/vancim/whats_agent/.venv"
PROJECT_PATH="/home/vancim/whats_agent"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

function show_help() {
    echo -e "${BLUE}WhatsApp Agent - Gerenciador de Servidor e Load Testing${NC}"
    echo ""
    echo "Uso: $0 [COMANDO]"
    echo ""
    echo "Comandos disponíveis:"
    echo "  start       Inicia o servidor em background"
    echo "  stop        Para o servidor"
    echo "  status      Verifica status do servidor"
    echo "  restart     Reinicia o servidor"
    echo "  test-load   Executa load testing (servidor deve estar rodando)"
    echo "  test-light  Executa apenas teste leve"
    echo "  test-demo   Demonstração completa (inicia servidor + testes)"
    echo "  help        Mostra esta ajuda"
    echo ""
}

function check_venv() {
    if [ ! -d "$VENV_PATH" ]; then
        echo -e "${RED}❌ Ambiente virtual não encontrado em $VENV_PATH${NC}"
        return 1
    fi
    return 0
}

function get_server_pid() {
    if [ -f "$SERVER_PID_FILE" ]; then
        cat "$SERVER_PID_FILE"
    else
        echo ""
    fi
}

function is_server_running() {
    local pid=$(get_server_pid)
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

function start_server() {
    echo -e "${BLUE}🚀 Iniciando WhatsApp Agent Server...${NC}"

    if ! check_venv; then
        return 1
    fi

    if is_server_running; then
        echo -e "${YELLOW}⚠️  Servidor já está rodando (PID: $(get_server_pid))${NC}"
        return 0
    fi

    cd "$PROJECT_PATH"

    # Ativar venv e iniciar servidor em background
    source "$VENV_PATH/bin/activate"

    # Iniciar servidor em background e capturar PID
    nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/whatsapp_agent.log 2>&1 &
    local server_pid=$!

    echo "$server_pid" > "$SERVER_PID_FILE"

    # Aguardar servidor inicializar
    echo -e "${YELLOW}⏳ Aguardando servidor inicializar...${NC}"
    sleep 8

    # Verificar se servidor está respondendo
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Servidor iniciado com sucesso!${NC}"
        echo -e "${GREEN}   PID: $server_pid${NC}"
        echo -e "${GREEN}   URL: http://localhost:8000${NC}"
        echo -e "${GREEN}   Logs: tail -f /tmp/whatsapp_agent.log${NC}"
        return 0
    else
        echo -e "${RED}❌ Servidor não respondeu ao health check${NC}"
        echo -e "${YELLOW}🔍 Verificando logs:${NC}"
        tail -20 /tmp/whatsapp_agent.log
        return 1
    fi
}

function stop_server() {
    echo -e "${BLUE}🛑 Parando WhatsApp Agent Server...${NC}"

    local pid=$(get_server_pid)

    if [ -z "$pid" ]; then
        echo -e "${YELLOW}⚠️  PID não encontrado${NC}"
        return 0
    fi

    if kill -0 "$pid" 2>/dev/null; then
        kill "$pid"
        sleep 3

        if kill -0 "$pid" 2>/dev/null; then
            echo -e "${YELLOW}⚠️  Forçando parada...${NC}"
            kill -9 "$pid"
        fi

        rm -f "$SERVER_PID_FILE"
        echo -e "${GREEN}✅ Servidor parado${NC}"
    else
        echo -e "${YELLOW}⚠️  Processo não encontrado (PID: $pid)${NC}"
        rm -f "$SERVER_PID_FILE"
    fi
}

function server_status() {
    local pid=$(get_server_pid)

    if [ -z "$pid" ]; then
        echo -e "${YELLOW}📊 Status: Servidor não está rodando${NC}"
        return 1
    fi

    if kill -0 "$pid" 2>/dev/null; then
        echo -e "${GREEN}📊 Status: Servidor rodando${NC}"
        echo -e "${GREEN}   PID: $pid${NC}"
        echo -e "${GREEN}   URL: http://localhost:8000${NC}"

        # Testar conectividade
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            echo -e "${GREEN}   Health: ✅ OK${NC}"
        else
            echo -e "${RED}   Health: ❌ Não responde${NC}"
        fi
        return 0
    else
        echo -e "${RED}📊 Status: PID existe mas processo morto${NC}"
        rm -f "$SERVER_PID_FILE"
        return 1
    fi
}

function run_load_tests() {
    echo -e "${BLUE}🧪 Executando Load Testing...${NC}"

    if ! check_venv; then
        return 1
    fi

    # Verificar se servidor está rodando
    if ! server_status > /dev/null; then
        echo -e "${RED}❌ Servidor não está rodando!${NC}"
        echo -e "${YELLOW}💡 Execute: $0 start${NC}"
        return 1
    fi

    cd "$PROJECT_PATH"
    source "$VENV_PATH/bin/activate"

    python tests/load/run_load_tests.py
    return $?
}

function run_light_test() {
    echo -e "${BLUE}🧪 Executando Teste Leve...${NC}"

    if ! check_venv; then
        return 1
    fi

    # Verificar se servidor está rodando
    if ! server_status > /dev/null; then
        echo -e "${RED}❌ Servidor não está rodando!${NC}"
        echo -e "${YELLOW}💡 Execute: $0 start${NC}"
        return 1
    fi

    cd "$PROJECT_PATH"
    source "$VENV_PATH/bin/activate"

    # Executar apenas teste leve
    locust -f tests/load/test_load_whatsapp.py --host=http://localhost:8000 --users=5 --spawn-rate=1 -t 30s --headless
    return $?
}

function demo_complete() {
    echo -e "${BLUE}🎬 Demonstração Completa - TRILHA 2 FASE 2.2${NC}"
    echo -e "${BLUE}============================================${NC}"

    # 1. Iniciar servidor
    echo -e "\n${YELLOW}Passo 1: Iniciando servidor...${NC}"
    start_server

    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Falha ao iniciar servidor${NC}"
        return 1
    fi

    # 2. Aguardar estabilização
    echo -e "\n${YELLOW}Passo 2: Aguardando estabilização...${NC}"
    sleep 5

    # 3. Executar teste leve
    echo -e "\n${YELLOW}Passo 3: Executando teste leve...${NC}"
    run_light_test

    # 4. Aguardar
    echo -e "\n${YELLOW}Passo 4: Pausa entre testes...${NC}"
    sleep 10

    # 5. Status final
    echo -e "\n${YELLOW}Passo 5: Status final...${NC}"
    server_status

    echo -e "\n${GREEN}✅ Demonstração concluída!${NC}"
    echo -e "${BLUE}💡 Servidor continua rodando para mais testes${NC}"
    echo -e "${BLUE}   Para parar: $0 stop${NC}"
    echo -e "${BLUE}   Para mais testes: $0 test-load${NC}"
}

# Main
case "$1" in
    start)
        start_server
        ;;
    stop)
        stop_server
        ;;
    status)
        server_status
        ;;
    restart)
        stop_server
        sleep 2
        start_server
        ;;
    test-load)
        run_load_tests
        ;;
    test-light)
        run_light_test
        ;;
    test-demo)
        demo_complete
        ;;
    help|--help|-h)
        show_help
        ;;
    "")
        show_help
        ;;
    *)
        echo -e "${RED}❌ Comando inválido: $1${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac
