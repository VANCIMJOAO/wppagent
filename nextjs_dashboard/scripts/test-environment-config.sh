#!/bin/bash

# Script de Teste de Configuração por Ambiente
# Valida se as configurações estão corretas para cada ambiente

echo "🧪 TESTANDO CONFIGURAÇÃO POR AMBIENTE"
echo "====================================="

cd "$(dirname "$0")/.."

# Cores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para testar ambiente
test_environment() {
    local env=$1
    local expected_url=$2
    
    echo -e "\n📋 Testando ambiente: ${YELLOW}${env}${NC}"
    
    # Exportar variáveis para o ambiente específico
    if [ -f ".env.${env}" ]; then
        export $(grep -v '^#' .env.${env} | xargs)
        echo "✅ Arquivo .env.${env} carregado"
    else
        echo -e "${RED}❌ Arquivo .env.${env} não encontrado${NC}"
        return 1
    fi
    
    # Verificar se a URL está correta
    if [ "${NEXT_PUBLIC_API_BASE_URL}" = "${expected_url}" ]; then
        echo -e "${GREEN}✅ URL correta: ${NEXT_PUBLIC_API_BASE_URL}${NC}"
    else
        echo -e "${RED}❌ URL incorreta. Esperado: ${expected_url}, Atual: ${NEXT_PUBLIC_API_BASE_URL}${NC}"
        return 1
    fi
    
    # Verificar outras configurações
    echo "📊 Configurações:"
    echo "   Environment: ${NEXT_PUBLIC_ENVIRONMENT}"
    echo "   Debug: ${NEXT_PUBLIC_ENABLE_DEBUG}"
    echo "   Timeout: ${NEXT_PUBLIC_REQUEST_TIMEOUT}"
    
    # Limpar variáveis
    unset NEXT_PUBLIC_API_BASE_URL NEXT_PUBLIC_ENVIRONMENT NEXT_PUBLIC_ENABLE_DEBUG NEXT_PUBLIC_REQUEST_TIMEOUT
}

# Testar cada ambiente
echo "🔍 Verificando arquivos de configuração..."

test_environment "development" "http://localhost:8000"
test_environment "staging" "https://wppagent-staging.up.railway.app" 
test_environment "production" "https://wppagent-production.up.railway.app"

# Verificar se não há URLs hardcoded
echo -e "\n🔍 Verificando URLs hardcoded..."
if grep -r "wppagent-production.up.railway.app" lib/ --include="*.ts" --include="*.tsx" | grep -v "fallback\|default" | grep -v ".env"; then
    echo -e "${RED}❌ URLs hardcoded encontradas!${NC}"
else
    echo -e "${GREEN}✅ Nenhuma URL hardcoded encontrada${NC}"
fi

# Verificar estrutura de arquivos
echo -e "\n📁 Verificando estrutura de arquivos..."
files=(".env.development" ".env.staging" ".env.production" ".env.example" "lib/environment-config.ts")

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✅ ${file}${NC}"
    else
        echo -e "${RED}❌ ${file} não encontrado${NC}"
    fi
done

echo -e "\n🎯 TESTE COMPLETO!"
echo "================="
