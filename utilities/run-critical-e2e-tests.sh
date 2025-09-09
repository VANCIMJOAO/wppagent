#!/bin/bash

# Script para executar testes E2E críticos do WhatsApp Agent Dashboard
# Executa todos os testes críticos e gera relatórios

set -e

echo "🧪 Iniciando Execução de Testes E2E Críticos"
echo "=============================================="
echo "Data/Hora: $(date)"
echo "Diretório: $(pwd)"
echo ""

# Navegar para diretório do dashboard
cd "$(dirname "$0")/nextjs_dashboard"

# Verificar se dependências estão instaladas
if [ ! -d "node_modules" ]; then
    echo "📦 Instalando dependências..."
    npm install
fi

# Verificar se Playwright está instalado
if [ ! -d "node_modules/@playwright/test" ]; then
    echo "📦 Instalando Playwright..."
    npm install @playwright/test
    npx playwright install
fi

# Criar diretório de relatórios se não existir
mkdir -p test-results/reports
mkdir -p test-results/screenshots

echo "🚀 Executando Testes E2E Críticos..."
echo ""

# Definir testes por categoria
declare -a CRITICAL_TESTS=(
    "auth-critical.spec.ts"
    "appointments-critical.spec.ts" 
    "messages-critical.spec.ts"
    "dashboard-critical.spec.ts"
    "performance-critical.spec.ts"
)

# Configurar variáveis de ambiente para testes
export NODE_ENV=test
export BASE_URL=${BASE_URL:-http://localhost:3000}

# Função para executar um conjunto de testes
run_test_suite() {
    local test_file=$1
    local test_name=$(basename "$test_file" .spec.ts)
    
    echo "📋 Executando: $test_name"
    echo "----------------------------------------"
    
    # Executar teste específico
    if npx playwright test "e2e/$test_file" --reporter=html --output-dir="test-results/$test_name"; then
        echo "✅ $test_name: PASSOU"
        return 0
    else
        echo "❌ $test_name: FALHOU"
        return 1
    fi
}

# Contador de resultados
PASSED=0
FAILED=0
TOTAL=${#CRITICAL_TESTS[@]}

# Executar cada teste crítico
for test in "${CRITICAL_TESTS[@]}"; do
    echo ""
    if run_test_suite "$test"; then
        ((PASSED++))
    else
        ((FAILED++))
    fi
done

# Executar todos os testes em paralelo para relatório consolidado
echo ""
echo "📊 Gerando Relatório Consolidado..."
npx playwright test e2e/ --reporter=html,json --output-dir=test-results/consolidated

# Gerar resumo
echo ""
echo "📈 RESUMO DA EXECUÇÃO"
echo "===================="
echo "Total de Suites: $TOTAL"
echo "Passou: $PASSED"
echo "Falhou: $FAILED"
echo "Taxa de Sucesso: $(( PASSED * 100 / TOTAL ))%"

# Mostrar localização dos relatórios
echo ""
echo "📁 Relatórios Gerados:"
echo "- HTML Report: test-results/consolidated/playwright-report/index.html"
echo "- JSON Report: test-results/consolidated/results.json"
echo "- Screenshots: test-results/screenshots/"

# Abrir relatório HTML se possível
if command -v xdg-open &> /dev/null; then
    echo ""
    echo "🌐 Abrindo relatório HTML..."
    xdg-open "test-results/consolidated/playwright-report/index.html" || true
elif command -v open &> /dev/null; then
    echo ""
    echo "🌐 Abrindo relatório HTML..."
    open "test-results/consolidated/playwright-report/index.html" || true
fi

# Status de saída
if [ $FAILED -eq 0 ]; then
    echo ""
    echo "🎉 Todos os testes E2E críticos passaram!"
    exit 0
else
    echo ""
    echo "💥 $FAILED suite(s) de teste falharam!"
    echo "Verifique os relatórios para detalhes."
    exit 1
fi
