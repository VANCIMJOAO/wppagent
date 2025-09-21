#!/bin/bash

echo "🧪 EXECUTOR DE TESTES COMPLETOS DO DASHBOARD NEXT.JS"
echo "===================================================="
echo ""

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para imprimir com cor
print_color() {
    echo -e "${1}${2}${NC}"
}

# Verificar se Node.js está instalado
if ! command -v node &> /dev/null; then
    print_color $RED "❌ Node.js não encontrado. Instale Node.js primeiro."
    exit 1
fi

# Verificar se npm está instalado
if ! command -v npm &> /dev/null; then
    print_color $RED "❌ npm não encontrado. Instale npm primeiro."
    exit 1
fi

print_color $GREEN "✅ Node.js e npm encontrados"

# Verificar se Playwright está instalado
if ! npx playwright --version &> /dev/null; then
    print_color $YELLOW "⚠️  Playwright não encontrado. Instalando..."
    npm install @playwright/test
    npx playwright install
    print_color $GREEN "✅ Playwright instalado com sucesso"
else
    print_color $GREEN "✅ Playwright encontrado"
fi

# Verificar se servidor está rodando
print_color $BLUE "🔍 Verificando se servidor está rodando..."

if curl -s http://localhost:3000 > /dev/null 2>&1; then
    print_color $GREEN "✅ Servidor está rodando em http://localhost:3000"
else
    print_color $YELLOW "⚠️  Servidor não está rodando."
    print_color $YELLOW "   Execute: npm run dev"
    print_color $YELLOW "   Aguarde o servidor iniciar e execute os testes novamente."
    exit 1
fi

echo ""
print_color $BLUE "🚀 Iniciando execução dos testes..."
echo ""

# Contadores
total_suites=0
passed_suites=0
failed_suites=0

# Array de conjuntos de testes
test_suites=(
    "dashboard-complete.spec.ts:Dashboard Completo - Todas as Funcionalidades"
    "crud-operations.spec.ts:CRUD Operations - Operações de Banco"
    "realtime-features.spec.ts:Funcionalidades em Tempo Real"
    "export-reports.spec.ts:Exportação e Relatórios"
    "auth-rbac.spec.ts:Autenticação e RBAC"
    "pwa-offline.spec.ts:PWA e Funcionalidades Offline"
)

# Executar cada conjunto de testes
for suite in "${test_suites[@]}"; do
    IFS=':' read -r file name <<< "$suite"
    total_suites=$((total_suites + 1))
    
    print_color $BLUE "🧪 Executando: $name"
    print_color $BLUE "   📁 Arquivo: $file"
    echo ""
    
    if npx playwright test "tests/$file" --reporter=html --quiet; then
        print_color $GREEN "✅ $name - PASSOU"
        passed_suites=$((passed_suites + 1))
    else
        print_color $RED "❌ $name - FALHOU"
        failed_suites=$((failed_suites + 1))
    fi
    
    echo ""
done

# Relatório final
print_color $BLUE "📈 RELATÓRIO FINAL:"
print_color $BLUE "=================="
print_color $BLUE "Total de Suites: $total_suites"
print_color $GREEN "✅ Passou: $passed_suites"
print_color $RED "❌ Falhou: $failed_suites"

# Calcular taxa de sucesso
if [ $total_suites -gt 0 ]; then
    success_rate=$(( (passed_suites * 100) / total_suites ))
    print_color $BLUE "📊 Taxa de Sucesso: ${success_rate}%"
else
    print_color $YELLOW "⚠️  Nenhum teste foi executado"
fi

echo ""

if [ $failed_suites -gt 0 ]; then
    print_color $YELLOW "🔍 Para ver detalhes dos testes que falharam:"
    print_color $YELLOW "   npx playwright show-report"
    echo ""
fi

if [ $passed_suites -eq $total_suites ]; then
    print_color $GREEN "🎉 TODOS OS TESTES PASSARAM!"
    print_color $GREEN "🎯 Dashboard está funcionando perfeitamente!"
else
    print_color $YELLOW "⚠️  Alguns testes falharam. Verifique os relatórios para detalhes."
fi

echo ""
print_color $BLUE "🎯 TESTES CONCLUÍDOS!"
print_color $BLUE "====================="
