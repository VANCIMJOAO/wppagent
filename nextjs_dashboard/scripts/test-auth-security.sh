#!/bin/bash

# Script de Teste de Segurança da Autenticação
# Verifica se não há tokens JWT em JavaScript client-side

echo "🔒 TESTE DE SEGURANÇA DE AUTENTICAÇÃO"
echo "===================================="

cd "$(dirname "$0")/.."

# Cores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para verificar arquivos
check_file_security() {
    local file=$1
    local issues=0

    echo -e "\n📁 Analisando: ${BLUE}${file}${NC}"

    # Verificar tokens JWT em JavaScript
    if grep -n "let.*token\|const.*token\|var.*token" "$file" | grep -v "// ❌\|// ✅" | grep -q "token"; then
        echo -e "${RED}❌ Variáveis de token encontradas${NC}"
        grep -n "let.*token\|const.*token\|var.*token" "$file" | head -3
        issues=$((issues + 1))
    fi

    # Verificar localStorage/sessionStorage
    if grep -qn "localStorage\|sessionStorage" "$file"; then
        echo -e "${YELLOW}⚠️  Uso de localStorage/sessionStorage detectado${NC}"
        grep -n "localStorage\|sessionStorage" "$file" | head -2
        issues=$((issues + 1))
    fi

    # Verificar headers Authorization hardcoded
    if grep -qn "Authorization.*Bearer\|authorization.*bearer" "$file"; then
        echo -e "${RED}❌ Headers Authorization hardcoded${NC}"
        grep -n "Authorization.*Bearer\|authorization.*bearer" "$file" | head -2
        issues=$((issues + 1))
    fi

    # Verificar imports seguros
    if grep -qn "secure-auth-manager\|HttpOnly\|credentials.*include" "$file"; then
        echo -e "${GREEN}✅ Imports seguros detectados${NC}"
    fi

    return $issues
}

echo "🔍 Verificando arquivos JavaScript/TypeScript..."

total_issues=0
files_checked=0

# Verificar arquivos principais
for file in lib/*.ts lib/*.tsx components/**/*.tsx app/**/*.tsx; do
    if [[ -f "$file" ]]; then
        check_file_security "$file"
        total_issues=$((total_issues + $?))
        files_checked=$((files_checked + 1))
    fi
done

echo -e "\n🔐 VERIFICAÇÕES DE SEGURANÇA:"
echo "========================="

# Verificar se secure-auth-manager existe
if [[ -f "lib/secure-auth-manager.ts" ]]; then
    echo -e "${GREEN}✅ SecureAuthManager implementado${NC}"
else
    echo -e "${RED}❌ SecureAuthManager não encontrado${NC}"
    total_issues=$((total_issues + 1))
fi

# Verificar API routes seguras
secure_routes=("app/api/auth/login/route.ts" "app/api/auth/logout/route.ts" "app/api/auth/status/route.ts")
for route in "${secure_routes[@]}"; do
    if [[ -f "$route" ]]; then
        echo -e "${GREEN}✅ $route${NC}"

        # Verificar HttpOnly
        if grep -q "httpOnly.*true" "$route"; then
            echo -e "    ${GREEN}→ HttpOnly ativado${NC}"
        else
            echo -e "    ${RED}→ HttpOnly não encontrado${NC}"
            total_issues=$((total_issues + 1))
        fi
    else
        echo -e "${RED}❌ $route não encontrado${NC}"
        total_issues=$((total_issues + 1))
    fi
done

# Verificar configuração segura
echo -e "\n🛡️ CONFIGURAÇÕES DE SEGURANÇA:"
echo "============================="

if grep -q "sameSite.*strict" app/api/auth/*/route.ts; then
    echo -e "${GREEN}✅ SameSite=strict configurado${NC}"
else
    echo -e "${RED}❌ SameSite=strict não encontrado${NC}"
    total_issues=$((total_issues + 1))
fi

if grep -q "secure.*isProduction" app/api/auth/*/route.ts; then
    echo -e "${GREEN}✅ Cookies seguros por ambiente${NC}"
else
    echo -e "${RED}❌ Configuração de cookies seguros não encontrada${NC}"
    total_issues=$((total_issues + 1))
fi

# Resultado final
echo -e "\n🎯 RESULTADO DO TESTE:"
echo "===================="
echo "Arquivos verificados: $files_checked"
echo "Problemas encontrados: $total_issues"

if [[ $total_issues -eq 0 ]]; then
    echo -e "${GREEN}🛡️ SISTEMA SEGURO! Nenhum problema de segurança encontrado.${NC}"
else
    echo -e "${RED}⚠️ VULNERABILIDADES ENCONTRADAS! $total_issues problemas precisam ser corrigidos.${NC}"
fi

echo -e "\n📋 CHECKLIST DE SEGURANÇA:"
echo "========================="
echo "🔐 Tokens JWT em HttpOnly cookies: $(grep -q 'httpOnly.*true' app/api/auth/*/route.ts && echo '✅' || echo '❌')"
echo "🚫 Sem tokens em JavaScript: $(! grep -q 'let.*token.*=.*[^/]' lib/*.ts && echo '✅' || echo '❌')"
echo "🍪 SameSite=strict: $(grep -q 'sameSite.*strict' app/api/auth/*/route.ts && echo '✅' || echo '❌')"
echo "🔒 Secure cookies em produção: $(grep -q 'secure.*isProduction' app/api/auth/*/route.ts && echo '✅' || echo '❌')"
echo "🔄 Auto-refresh de tokens: $(test -f 'app/api/auth/refresh/route.ts' && echo '✅' || echo '❌')"

exit $total_issues
