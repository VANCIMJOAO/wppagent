#!/bin/bash

# =========================================================================
# WHATSAPP AGENT - SCRIPT DE STATUS RÁPIDO
# =========================================================================
# Este script mostra um resumo rápido do status da aplicação
# Criado em: 11 de Agosto de 2025
# Versão: 1.0.0
# =========================================================================

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
WHITE='\033[1;37m'
NC='\033[0m'

# Banner rápido
echo -e "${BLUE}🔍 WhatsApp Agent - Status Rápido${NC}"
echo "=================================="

# Verificar containers
echo -e "${YELLOW}📦 Containers:${NC}"
if command -v docker-compose &> /dev/null; then
    if docker-compose ps | grep -q "Up"; then
        local running=$(docker-compose ps --services --filter "status=running" | wc -l)
        local total=$(docker-compose ps --services | wc -l)
        echo -e "   ${GREEN}✅ $running/$total containers rodando${NC}"
    else
        echo -e "   ${RED}❌ Nenhum container rodando${NC}"
    fi
else
    echo -e "   ${RED}❌ Docker Compose não encontrado${NC}"
fi

# Verificar serviços principais
echo -e "${YELLOW}🌐 Serviços:${NC}"

# API Principal
if curl -s -o /dev/null --max-time 2 "http://localhost:8000/health" 2>/dev/null; then
    echo -e "   ${GREEN}✅ API Principal (8000)${NC}"
else
    echo -e "   ${RED}❌ API Principal (8000)${NC}"
fi

# Dashboard
if curl -s -o /dev/null --max-time 2 "http://localhost:8501" 2>/dev/null; then
    echo -e "   ${GREEN}✅ Dashboard (8501)${NC}"
else
    echo -e "   ${RED}❌ Dashboard (8501)${NC}"
fi

# PostgreSQL
if timeout 2 bash -c "cat < /dev/null > /dev/tcp/localhost/5432" 2>/dev/null; then
    echo -e "   ${GREEN}✅ PostgreSQL (5432)${NC}"
else
    echo -e "   ${RED}❌ PostgreSQL (5432)${NC}"
fi

# Redis
if timeout 2 bash -c "cat < /dev/null > /dev/tcp/localhost/6379" 2>/dev/null; then
    echo -e "   ${GREEN}✅ Redis (6379)${NC}"
else
    echo -e "   ${RED}❌ Redis (6379)${NC}"
fi

# Verificar logs de erro recentes
echo -e "${YELLOW}📋 Logs recentes:${NC}"
if docker-compose ps | grep -q "Up"; then
    local error_count=$(docker-compose logs --tail=50 2>/dev/null | grep -i error | wc -l || echo 0)
    if [[ $error_count -gt 0 ]]; then
        echo -e "   ${YELLOW}⚠️  $error_count erros encontrados nos logs${NC}"
    else
        echo -e "   ${GREEN}✅ Nenhum erro nos logs recentes${NC}"
    fi
else
    echo -e "   ${YELLOW}⚠️  Containers não rodando${NC}"
fi

# Comandos úteis
echo ""
echo -e "${BLUE}🔧 Comandos úteis:${NC}"
echo "   ./scripts/start_complete_application.sh  # Iniciar tudo"
echo "   ./scripts/stop_complete_application.sh   # Parar tudo"
echo "   ./scripts/monitor_application.sh         # Monitor em tempo real"
echo "   docker-compose logs -f                   # Ver logs"

echo ""
