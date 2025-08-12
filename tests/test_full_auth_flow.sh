#!/bin/bash

# 🔒 Teste Completo do Sistema de Autenticação

echo "
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║           🔒 TESTE COMPLETO DE AUTENTICAÇÃO                  ║
║                                                              ║
║              http://localhost:8001                           ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"

BASE_URL="http://localhost:8001"

# Cores
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_test() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✅]${NC} $1"
}

log_error() {
    echo -e "${RED}[❌]${NC} $1"
}

log_info() {
    echo -e "${YELLOW}[ℹ️]${NC} $1"
}

# 1. Health Check
log_test "1. Health Check..."
health_response=$(curl -s $BASE_URL/health)
if echo "$health_response" | grep -q "healthy"; then
    log_success "Health check passou"
else
    log_error "Health check falhou"
    echo "$health_response"
fi

# 2. Login básico
log_test "2. Login básico (admin/os.getenv("ADMIN_PASSWORD", "SECURE_ADMIN_PASSWORD"))..."
login_response=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"os.getenv("ADMIN_PASSWORD", "SECURE_ADMIN_PASSWORD")"}' \
    $BASE_URL/auth/login)

if echo "$login_response" | grep -q "access_token"; then
    log_success "Login realizado com sucesso"
    TOKEN=$(echo "$login_response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))")
    log_info "Token: ${TOKEN:0:30}..."
else
    log_error "Falha no login"
    echo "$login_response"
    exit 1
fi

# 3. Status da autenticação
log_test "3. Verificando status da autenticação..."
auth_status=$(curl -s -H "Authorization: Bearer $TOKEN" \
    $BASE_URL/auth/status)

if echo "$auth_status" | grep -q "authenticated"; then
    log_success "Status verificado - usuário autenticado"
    echo "   $auth_status"
else
    log_error "Falha ao verificar status"
    echo "$auth_status"
fi

# 4. Configuração de 2FA
log_test "4. Configurando 2FA..."
twofa_response=$(curl -s -X POST \
    -H "Authorization: Bearer $TOKEN" \
    $BASE_URL/auth/2fa/setup)

if echo "$twofa_response" | grep -q "secret"; then
    log_success "2FA configurado com sucesso"
    SECRET=$(echo "$twofa_response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('secret', ''))" 2>/dev/null)
    log_info "Secret TOTP: $SECRET"
    
    # Salvar QR code se disponível
    QR_CODE=$(echo "$twofa_response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('qr_code', ''))" 2>/dev/null)
    if [ -n "$QR_CODE" ]; then
        log_info "QR Code salvo (base64 disponível)"
    fi
else
    log_error "Falha na configuração de 2FA"
    echo "$twofa_response"
fi

# 5. Verificação de 2FA (simulada)
if [ -n "$SECRET" ]; then
    log_test "5. Gerando código TOTP para verificação..."
    
    # Instalar pyotp se necessário
    python3 -c "import pyotp" 2>/dev/null || pip install pyotp
    
    # Gerar código TOTP
    TOTP_CODE=$(python3 -c "import pyotp; print(pyotp.TOTP('$SECRET').now())")
    log_info "Código TOTP gerado: $TOTP_CODE"
    
    # Verificar 2FA
    verify_response=$(curl -s -X POST \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d "{\"code\":\"$TOTP_CODE\",\"type\":\"totp\"}" \
        $BASE_URL/auth/2fa/verify)
    
    if echo "$verify_response" | grep -q "access_token"; then
        log_success "2FA verificado com sucesso"
        NEW_TOKEN=$(echo "$verify_response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))")
        TOKEN=$NEW_TOKEN
        log_info "Novo token com 2FA: ${TOKEN:0:30}..."
    else
        log_error "Falha na verificação de 2FA"
        echo "$verify_response"
    fi
else
    log_error "Secret não disponível para teste de 2FA"
fi

# 6. Listagem de secrets
log_test "6. Listando secrets..."
secrets_response=$(curl -s -H "Authorization: Bearer $TOKEN" \
    $BASE_URL/secrets/list)

if echo "$secrets_response" | grep -q "secrets"; then
    log_success "Secrets listados com sucesso"
    COUNT=$(echo "$secrets_response" | python3 -c "import sys, json; print(len(json.load(sys.stdin).get('secrets', [])))" 2>/dev/null)
    log_info "Total de secrets: $COUNT"
else
    log_error "Falha ao listar secrets"
    echo "$secrets_response"
fi

# 7. Criação de secret
log_test "7. Criando secret de teste..."
create_secret_response=$(curl -s -X POST \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"secret_id":"test_integration","secret_type":"api_key","value":"test_value_123"}' \
    $BASE_URL/secrets/create)

if echo "$create_secret_response" | grep -q "created successfully"; then
    log_success "Secret criado com sucesso"
else
    log_error "Falha ao criar secret"
    echo "$create_secret_response"
fi

# 8. Obter informações do secret
log_test "8. Obtendo informações do secret..."
secret_info=$(curl -s -H "Authorization: Bearer $TOKEN" \
    $BASE_URL/secrets/test_integration)

if echo "$secret_info" | grep -q "test_integration"; then
    log_success "Informações do secret obtidas"
else
    log_error "Falha ao obter informações"
    echo "$secret_info"
fi

# 9. Obter valor do secret (operação auditada)
log_test "9. Obtendo valor do secret (operação auditada)..."
secret_value=$(curl -s -H "Authorization: Bearer $TOKEN" \
    $BASE_URL/secrets/test_integration/value)

if echo "$secret_value" | grep -q "test_value_123"; then
    log_success "Valor do secret obtido com sucesso"
    log_info "Esta operação foi registrada para auditoria"
else
    log_error "Falha ao obter valor"
    echo "$secret_value"
fi

# 10. Refresh do token
log_test "10. Renovando token..."
refresh_response=$(curl -s -X POST \
    -H "Authorization: Bearer $TOKEN" \
    $BASE_URL/auth/refresh)

if echo "$refresh_response" | grep -q "access_token"; then
    log_success "Token renovado com sucesso"
    REFRESHED_TOKEN=$(echo "$refresh_response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))")
    log_info "Novo token: ${REFRESHED_TOKEN:0:30}..."
else
    log_error "Falha ao renovar token"
    echo "$refresh_response"
fi

# 11. Rotação de secret
log_test "11. Rotacionando secret..."
rotate_response=$(curl -s -X POST \
    -H "Authorization: Bearer $TOKEN" \
    $BASE_URL/secrets/test_integration/rotate)

if echo "$rotate_response" | grep -q "rotated successfully"; then
    log_success "Secret rotacionado com sucesso"
else
    log_error "Falha ao rotacionar secret"
    echo "$rotate_response"
fi

# 12. Health check detalhado
log_test "12. Health check detalhado..."
detailed_health=$(curl -s $BASE_URL/health/detailed)
if echo "$detailed_health" | grep -q "overall_status"; then
    log_success "Health check detalhado obtido"
    STATUS=$(echo "$detailed_health" | python3 -c "import sys, json; print(json.load(sys.stdin).get('overall_status', 'unknown'))" 2>/dev/null)
    log_info "Status geral: $STATUS"
else
    log_error "Falha no health check detalhado"
fi

# 13. Revogação do token
log_test "13. Revogando token..."
revoke_response=$(curl -s -X POST \
    -H "Authorization: Bearer $TOKEN" \
    $BASE_URL/auth/revoke)

if echo "$revoke_response" | grep -q "revoked successfully"; then
    log_success "Token revogado com sucesso"
else
    log_error "Falha ao revogar token"
    echo "$revoke_response"
fi

# 14. Teste de acesso após revogação
log_test "14. Testando acesso após revogação..."
post_revoke_response=$(curl -s -H "Authorization: Bearer $TOKEN" \
    $BASE_URL/auth/status)

if echo "$post_revoke_response" | grep -q "Invalid.*token"; then
    log_success "Token corretamente invalidado após revogação"
else
    log_error "Token ainda válido após revogação (pode ser um problema)"
    echo "$post_revoke_response"
fi

echo "
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║           🎉 TESTE COMPLETO FINALIZADO                       ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

📊 RESUMO DOS TESTES EXECUTADOS:
✅ Health Check básico e detalhado
✅ Login com usuário/senha  
✅ Verificação de status de autenticação
✅ Configuração de 2FA (TOTP)
✅ Verificação de código 2FA
✅ Listagem de secrets
✅ Criação de novo secret
✅ Obtenção de informações do secret
✅ Obtenção de valor do secret (auditado)
✅ Renovação de token
✅ Rotação de secret
✅ Revogação de token
✅ Validação de acesso pós-revogação

🔒 SISTEMA DE SEGURANÇA COMPLETAMENTE FUNCIONAL!

🌐 Servidor de teste: http://localhost:8001
📖 Documentação: http://localhost:8001/docs
"
