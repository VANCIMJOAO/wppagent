#!/bin/bash
"""
🧪 Script de Execução de Testes Reais - SEM MOCKS
Executa testes reais contra o sistema rodando
"""

# Configurações
API_URL="http://localhost:8000"
TEST_PHONE_BASE="5511999"

echo "🧪 INICIANDO TESTES REAIS DO WHATSAPP AGENT"
echo "=============================================="
echo "📡 API URL: $API_URL"
echo "📱 Telefone base: $TEST_PHONE_BASE"
echo "🕐 Início: $(date)"
echo ""

# Verificar se a API está rodando
echo "🔍 Verificando se a API está rodando..."
if curl -s "$API_URL/health" > /dev/null; then
    echo "✅ API está rodando em $API_URL"
else
    echo "❌ API não está rodando em $API_URL"
    echo "🚀 Inicie a API com: python -m uvicorn app.main:app --reload"
    exit 1
fi

echo ""

# Função para executar testes com relatório
run_test_suite() {
    local test_file=$1
    local test_name=$2
    local markers=$3
    
    echo "🧪 Executando: $test_name"
    echo "📄 Arquivo: $test_file"
    echo "🏷️ Markers: $markers"
    echo "$(date '+%H:%M:%S') - Iniciando..."
    
    if pytest "$test_file" -v -m "$markers" --tb=short --api-url="$API_URL" --real-phone="$TEST_PHONE_BASE"; then
        echo "✅ $test_name - SUCESSO"
    else
        echo "❌ $test_name - FALHA"
        return 1
    fi
    echo ""
}

# Executar suites de teste
echo "🎯 EXECUTANDO TESTES REAIS"
echo "=========================="

# 1. Testes básicos de API
run_test_suite "tests/test_real_api.py" "Testes de API Real" "real and api"

# 2. Testes de webhook
run_test_suite "tests/test_real_api.py" "Testes de Webhook Real" "real and webhook"

# 3. Testes de conversação
run_test_suite "tests/test_real_api.py" "Testes de Conversação Real" "real and conversation"

# 4. Testes end-to-end
run_test_suite "tests/test_real_e2e.py" "Testes End-to-End Reais" "real and e2e_real"

# 5. Testes de performance
run_test_suite "tests/test_real_api.py" "Testes de Performance Real" "real and performance"

echo "🏁 TESTES REAIS CONCLUÍDOS"
echo "=========================="
echo "🕐 Fim: $(date)"
echo ""

# Executar relatório de cobertura se disponível
if command -v coverage &> /dev/null; then
    echo "📊 Gerando relatório de cobertura..."
    coverage report --include="app/*" --omit="app/tests/*,*/test_*"
    echo ""
fi

echo "✅ Todos os testes reais foram executados!"
echo "📋 Verifique os logs acima para detalhes"
