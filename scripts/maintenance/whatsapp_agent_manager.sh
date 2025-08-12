#!/bin/bash

# =========================================================================
# WHATSAPP AGENT - MENU PRINCIPAL DE GESTÃO
# =========================================================================
# Menu interativo para gerenciar toda a aplicação WhatsApp Agent
# Criado em: 11 de Agosto de 2025
# Versão: 1.0.0
# =========================================================================

set -e

# Detectar comando Docker Compose
detect_docker_compose() {
    if command -v docker-compose &> /dev/null; then
        DOCKER_COMPOSE_CMD="docker-compose"
    elif docker compose version &> /dev/null 2>&1; then
        DOCKER_COMPOSE_CMD="docker compose"
    else
        return 1
    fi
    return 0
}

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m'

# Função para limpar tela e mostrar banner
show_banner() {
    clear
    echo -e "${PURPLE}"
    echo "==========================================================================="
    echo "                      🚀 WHATSAPP AGENT MANAGER 🚀"
    echo "==========================================================================="
    echo "                    Sistema de Gestão Completa da Aplicação"
    echo "                           Versão: 1.0.0 | $(date '+%Y-%m-%d')"
    echo "==========================================================================="
    echo -e "${NC}"
}

# Mostrar status atual
show_current_status() {
    echo -e "${CYAN}📊 STATUS ATUAL:${NC}"
    echo "=================="
    
    # Verificar containers
    if detect_docker_compose; then
        if $DOCKER_COMPOSE_CMD ps | grep -q "Up" 2>/dev/null; then
            local running=$($DOCKER_COMPOSE_CMD ps --services --filter "status=running" 2>/dev/null | wc -l)
            local total=$($DOCKER_COMPOSE_CMD ps --services 2>/dev/null | wc -l)
            echo -e "🐳 Containers: ${GREEN}$running/$total rodando${NC}"
        else
            echo -e "🐳 Containers: ${RED}Nenhum rodando${NC}"
        fi
    else
        echo -e "🐳 Containers: ${RED}Docker Compose não encontrado${NC}"
    fi
    
    # Verificar serviços principais
    local api_status="${RED}❌${NC}"
    local dashboard_status="${RED}❌${NC}"
    local db_status="${RED}❌${NC}"
    local redis_status="${RED}❌${NC}"
    
    if curl -s -o /dev/null --max-time 2 "http://localhost:8000/health" 2>/dev/null; then
        api_status="${GREEN}✅${NC}"
    fi
    
    if curl -s -o /dev/null --max-time 2 "http://localhost:8501" 2>/dev/null; then
        dashboard_status="${GREEN}✅${NC}"
    fi
    
    if timeout 2 bash -c "cat < /dev/null > /dev/tcp/localhost/5432" 2>/dev/null; then
        db_status="${GREEN}✅${NC}"
    fi
    
    if timeout 2 bash -c "cat < /dev/null > /dev/tcp/localhost/6379" 2>/dev/null; then
        redis_status="${GREEN}✅${NC}"
    fi
    
    echo -e "🔗 API Principal (8000): $api_status"
    echo -e "📊 Dashboard (8501): $dashboard_status"
    echo -e "🗄️  PostgreSQL (5432): $db_status"
    echo -e "⚡ Redis (6379): $redis_status"
    echo ""
}

# Menu principal
show_main_menu() {
    echo -e "${WHITE}🎯 MENU PRINCIPAL:${NC}"
    echo "==================="
    echo ""
    echo -e "${GREEN} 1.${NC} 🚀 Iniciar Aplicação Completa"
    echo -e "${RED} 2.${NC} 🛑 Parar Aplicação"
    echo -e "${YELLOW} 3.${NC} 🔄 Reiniciar Aplicação"
    echo -e "${BLUE} 4.${NC} 🔍 Monitor em Tempo Real"
    echo -e "${CYAN} 5.${NC} 📊 Status Rápido"
    echo -e "${PURPLE} 6.${NC} 📋 Ver Logs"
    echo ""
    echo -e "${WHITE}🔧 FERRAMENTAS AVANÇADAS:${NC}"
    echo "=========================="
    echo -e "${GREEN} 7.${NC} 🧹 Limpeza Completa (cuidado!)"
    echo -e "${BLUE} 8.${NC} 🔧 Rebuild Containers"
    echo -e "${YELLOW} 9.${NC} 📚 Abrir Documentação HTML"
    echo -e "${CYAN}10.${NC} ⚙️  Configurar Ambiente (.env)"
    echo ""
    echo -e "${WHITE}📊 MONITORAMENTO:${NC}"
    echo "=================="
    echo -e "${GREEN}11.${NC} 🐳 Status Detalhado dos Containers"
    echo -e "${BLUE}12.${NC} 🌐 Teste de Conectividade"
    echo -e "${YELLOW}13.${NC} 📈 Recursos do Sistema"
    echo -e "${PURPLE}14.${NC} 🗄️  Status do Banco de Dados"
    echo ""
    echo -e "${RED} 0.${NC} 🚪 Sair"
    echo ""
    echo -e "${WHITE}==========================================================================${NC}"
}

# Executar opção selecionada
execute_option() {
    local option=$1
    
    case $option in
        1)
            echo -e "${GREEN}🚀 Iniciando aplicação completa...${NC}"
            echo ""
            ./scripts/start_complete_application.sh
            ;;
        2)
            echo -e "${RED}🛑 Parando aplicação...${NC}"
            echo ""
            read -p "Tem certeza? (y/N): " -n 1 -r
            echo ""
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                ./scripts/stop_complete_application.sh
            else
                echo "Operação cancelada."
            fi
            ;;
        3)
            echo -e "${YELLOW}🔄 Reiniciando aplicação...${NC}"
            echo ""
            ./scripts/stop_complete_application.sh
            sleep 3
            ./scripts/start_complete_application.sh
            ;;
        4)
            echo -e "${BLUE}🔍 Abrindo monitor em tempo real...${NC}"
            echo ""
            ./scripts/monitor_application.sh
            ;;
        5)
            echo -e "${CYAN}📊 Status rápido:${NC}"
            echo ""
            ./scripts/quick_status.sh
            echo ""
            read -p "Pressione Enter para continuar..."
            ;;
        6)
            echo -e "${PURPLE}📋 Logs da aplicação:${NC}"
            echo ""
            if $DOCKER_COMPOSE_CMD ps | grep -q "Up" 2>/dev/null; then
                echo "Pressione Ctrl+C para sair dos logs"
                sleep 2
                $DOCKER_COMPOSE_CMD logs -f
            else
                echo -e "${YELLOW}⚠️  Nenhum container rodando${NC}"
                read -p "Pressione Enter para continuar..."
            fi
            ;;
        7)
            echo -e "${RED}🧹 ATENÇÃO: Limpeza completa remove TODOS os dados!${NC}"
            echo ""
            read -p "Digite 'CONFIRMAR' para continuar: " confirm
            if [[ "$confirm" == "CONFIRMAR" ]]; then
                ./scripts/stop_complete_application.sh --clean
                docker system prune -af
                echo -e "${GREEN}✅ Limpeza completa realizada${NC}"
            else
                echo "Operação cancelada."
            fi
            read -p "Pressione Enter para continuar..."
            ;;
        8)
            echo -e "${BLUE}🔧 Reconstruindo containers...${NC}"
            echo ""
            docker-compose down
            docker-compose build --no-cache
            echo -e "${GREEN}✅ Containers reconstruídos${NC}"
            read -p "Pressione Enter para continuar..."
            ;;
        9)
            echo -e "${YELLOW}📚 Abrindo documentação HTML...${NC}"
            echo ""
            if [[ -f "docs/DOCUMENTACAO_COMPLETA.html" ]]; then
                if command -v xdg-open &> /dev/null; then
                    xdg-open "docs/DOCUMENTACAO_COMPLETA.html"
                elif command -v open &> /dev/null; then
                    open "docs/DOCUMENTACAO_COMPLETA.html"
                else
                    echo "Documentação disponível em: file://$(pwd)/docs/DOCUMENTACAO_COMPLETA.html"
                fi
                echo -e "${GREEN}✅ Documentação aberta no navegador${NC}"
            else
                echo -e "${RED}❌ Arquivo de documentação não encontrado${NC}"
            fi
            read -p "Pressione Enter para continuar..."
            ;;
        10)
            echo -e "${CYAN}⚙️  Configurando ambiente...${NC}"
            echo ""
            if [[ -f ".env" ]]; then
                echo "Arquivo .env atual:"
                echo "==================="
                grep -v "PASSWORD\|SECRET\|KEY\|TOKEN" .env | head -10
                echo ""
                read -p "Editar arquivo .env? (y/N): " -n 1 -r
                echo ""
                if [[ $REPLY =~ ^[Yy]$ ]]; then
                    ${EDITOR:-nano} .env
                fi
            else
                echo -e "${YELLOW}⚠️  Arquivo .env não encontrado${NC}"
                if [[ -f ".env.example" ]]; then
                    cp .env.example .env
                    echo -e "${GREEN}✅ Arquivo .env criado a partir do .env.example${NC}"
                    ${EDITOR:-nano} .env
                fi
            fi
            read -p "Pressione Enter para continuar..."
            ;;
        11)
            echo -e "${GREEN}🐳 Status detalhado dos containers:${NC}"
            echo ""
            ./scripts/monitor_application.sh containers
            ;;
        12)
            echo -e "${BLUE}🌐 Teste de conectividade:${NC}"
            echo ""
            ./scripts/monitor_application.sh services
            ;;
        13)
            echo -e "${YELLOW}📈 Recursos do sistema:${NC}"
            echo ""
            ./scripts/monitor_application.sh resources
            ;;
        14)
            echo -e "${PURPLE}🗄️  Status do banco de dados:${NC}"
            echo ""
            ./scripts/monitor_application.sh database
            ;;
        0)
            echo -e "${GREEN}👋 Obrigado por usar o WhatsApp Agent Manager!${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}❌ Opção inválida. Tente novamente.${NC}"
            sleep 1
            ;;
    esac
}

# Verificar diretório
check_directory() {
    if [[ ! -f "docker-compose.yml" ]] || [[ ! -d "scripts" ]]; then
        echo -e "${RED}❌ Execute este script a partir da raiz do projeto WhatsApp Agent${NC}"
        exit 1
    fi
}

# Loop principal
main_loop() {
    while true; do
        show_banner
        show_current_status
        show_main_menu
        
        echo -n -e "${WHITE}Escolha uma opção [0-14]: ${NC}"
        read -r option
        echo ""
        
        execute_option "$option"
    done
}

# Verificar argumentos da linha de comando
if [[ $# -gt 0 ]]; then
    case $1 in
        --help|-h)
            echo "WhatsApp Agent Manager"
            echo ""
            echo "Uso: $0 [opção]"
            echo ""
            echo "Execução sem argumentos abre o menu interativo."
            echo ""
            echo "Opções diretas:"
            echo "  start     Inicia a aplicação"
            echo "  stop      Para a aplicação"
            echo "  restart   Reinicia a aplicação"
            echo "  status    Mostra status rápido"
            echo "  monitor   Abre monitor em tempo real"
            echo "  logs      Mostra logs"
            exit 0
            ;;
        start)
            ./scripts/start_complete_application.sh
            exit 0
            ;;
        stop)
            ./scripts/stop_complete_application.sh
            exit 0
            ;;
        restart)
            ./scripts/stop_complete_application.sh
            sleep 3
            ./scripts/start_complete_application.sh
            exit 0
            ;;
        status)
            ./scripts/quick_status.sh
            exit 0
            ;;
        monitor)
            ./scripts/monitor_application.sh
            exit 0
            ;;
        logs)
            docker-compose logs -f
            exit 0
            ;;
        *)
            echo -e "${RED}❌ Opção desconhecida: $1${NC}"
            echo "Use --help para ver as opções disponíveis."
            exit 1
            ;;
    esac
fi

# Executar verificações e iniciar loop principal
check_directory
main_loop
