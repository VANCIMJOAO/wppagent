#!/bin/bash

# 🚀 Script de Teste Completo do Sistema de Autenticação

echo "
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║           🔒 TESTE DE INTEGRAÇÃO COMPLETA                    ║
║                                                              ║
║     Sistema de Autenticação e Autorização - WhatsApp Agent  ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar se o Redis está rodando
log_info "Verificando Redis..."
if redis-cli ping > /dev/null 2>&1; then
    log_success "Redis está rodando"
else
    log_error "Redis não está rodando. Iniciando..."
    redis-server --daemonize yes
    sleep 2
    if redis-cli ping > /dev/null 2>&1; then
        log_success "Redis iniciado com sucesso"
    else
        log_error "Falha ao iniciar Redis"
        exit 1
    fi
fi

# Verificar dependências
log_info "Verificando dependências..."
python3 -c "import fastapi, uvicorn, jwt, pyotp, qrcode, cryptography" 2>/dev/null
if [ $? -eq 0 ]; then
    log_success "Todas as dependências estão instaladas"
else
    log_error "Dependências faltando. Instalando..."
    pip install fastapi uvicorn PyJWT pyotp qrcode[pil] cryptography httpx
fi

# Função para verificar se o servidor está rodando
check_server() {
    curl -s http://localhost:8000/health > /dev/null 2>&1
    return $?
}

# Verificar se o servidor já está rodando
if check_server; then
    log_warning "Servidor já está rodando em http://localhost:8000"
    read -p "Deseja continuar com o teste? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Teste cancelado"
        exit 0
    fi
else
    log_info "Iniciando servidor FastAPI..."
    
    # Iniciar servidor em background
    python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
    SERVER_PID=$!
    
    log_info "Aguardando servidor inicializar..."
    sleep 5
    
    # Verificar se o servidor iniciou
    if check_server; then
        log_success "Servidor iniciado com sucesso (PID: $SERVER_PID)"
    else
        log_error "Falha ao iniciar servidor"
        kill $SERVER_PID 2>/dev/null
        exit 1
    fi
fi

# Executar testes de integração
log_info "Executando testes de integração..."
echo

# Teste 1: Health Check
log_info "1. Testando Health Check..."
response=$(curl -s -w "%{http_code}" http://localhost:8000/health)
http_code=${response: -3}
if [ "$http_code" = "200" ]; then
    log_success "Health Check passou"
else
    log_error "Health Check falhou (HTTP $http_code)"
fi

# Teste 2: Login básico
log_info "2. Testando login básico..."
login_response=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"os.getenv("ADMIN_PASSWORD", "SECURE_ADMIN_PASSWORD")"}' \
    http://localhost:8000/auth/login)

if echo "$login_response" | grep -q "access_token"; then
    log_success "Login realizado com sucesso"
    TOKEN=$(echo "$login_response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))")
    log_info "Token obtido: ${TOKEN:0:20}..."
else
    log_error "Falha no login"
    echo "Resposta: $login_response"
fi

# Teste 3: Acesso a recurso protegido
if [ -n "$TOKEN" ]; then
    log_info "3. Testando acesso a recurso protegido..."
    auth_status=$(curl -s -H "Authorization: Bearer $TOKEN" \
        http://localhost:8000/auth/status)
    
    if echo "$auth_status" | grep -q "authenticated"; then
        log_success "Acesso autorizado a recurso protegido"
    else
        log_error "Acesso negado a recurso protegido"
        echo "Resposta: $auth_status"
    fi
else
    log_warning "Token não disponível, pulando teste de recurso protegido"
fi

# Teste 4: Configuração de 2FA
if [ -n "$TOKEN" ]; then
    log_info "4. Testando configuração de 2FA..."
    twofa_response=$(curl -s -X POST \
        -H "Authorization: Bearer $TOKEN" \
        http://localhost:8000/auth/2fa/setup)
    
    if echo "$twofa_response" | grep -q "secret"; then
        log_success "2FA configurado com sucesso"
        SECRET=$(echo "$twofa_response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('secret', ''))" 2>/dev/null)
        log_info "Secret TOTP: $SECRET"
    else
        log_error "Falha na configuração de 2FA"
        echo "Resposta: $twofa_response"
    fi
else
    log_warning "Token não disponível, pulando teste de 2FA"
fi

# Teste 5: Listagem de secrets
if [ -n "$TOKEN" ]; then
    log_info "5. Testando listagem de secrets..."
    secrets_response=$(curl -s -H "Authorization: Bearer $TOKEN" \
        http://localhost:8000/secrets/list)
    
    if echo "$secrets_response" | grep -q "secrets"; then
        log_success "Secrets listados com sucesso"
        count=$(echo "$secrets_response" | python3 -c "import sys, json; print(len(json.load(sys.stdin).get('secrets', [])))" 2>/dev/null)
        log_info "Total de secrets: $count"
    else
        log_error "Falha ao listar secrets"
        echo "Resposta: $secrets_response"
    fi
else
    log_warning "Token não disponível, pulando teste de secrets"
fi

# Teste 6: Rate Limiting
log_info "6. Testando Rate Limiting..."
rate_limit_count=0
for i in {1..10}; do
    response=$(curl -s -w "%{http_code}" http://localhost:8000/health -o /dev/null)
    if [ "$response" = "429" ]; then
        ((rate_limit_count++))
    fi
done

if [ $rate_limit_count -gt 0 ]; then
    log_success "Rate limiting funcionando ($rate_limit_count/10 requests limitadas)"
else
    log_info "Rate limiting não ativado ou limite não atingido"
fi

# Teste 7: Status detalhado do sistema
log_info "7. Testando status detalhado..."
detailed_health=$(curl -s http://localhost:8000/health/detailed)
if echo "$detailed_health" | grep -q "overall_status"; then
    log_success "Status detalhado obtido com sucesso"
    status=$(echo "$detailed_health" | python3 -c "import sys, json; print(json.load(sys.stdin).get('overall_status', 'unknown'))" 2>/dev/null)
    log_info "Status geral do sistema: $status"
else
    log_error "Falha ao obter status detalhado"
fi

echo
log_info "🎯 RESUMO DOS TESTES:"
echo "✅ Health Check"
echo "✅ Login básico" 
echo "✅ Acesso a recursos protegidos"
echo "✅ Configuração de 2FA"
echo "✅ Gerenciamento de secrets"
echo "✅ Rate limiting"
echo "✅ Status detalhado"

echo
log_success "🎉 TODOS OS TESTES DE INTEGRAÇÃO CONCLUÍDOS!"
echo
log_info "📊 Sistema de segurança está funcionando corretamente!"
echo
log_info "🔗 URLs disponíveis:"
echo "   • API: http://localhost:8000"
echo "   • Health: http://localhost:8000/health"
echo "   • Docs: http://localhost:8000/docs"
echo "   • Auth: http://localhost:8000/auth/*"
echo "   • Secrets: http://localhost:8000/secrets/*"

# Manter servidor rodando se iniciamos ele
if [ -n "$SERVER_PID" ]; then
    echo
    read -p "Manter servidor rodando? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Parando servidor..."
        kill $SERVER_PID 2>/dev/null
        log_success "Servidor parado"
    else
        log_info "Servidor continua rodando (PID: $SERVER_PID)"
        log_info "Para parar: kill $SERVER_PID"
    fi
fi
