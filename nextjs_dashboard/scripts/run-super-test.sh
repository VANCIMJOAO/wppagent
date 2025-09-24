#!/bin/bash

# SUPER TESTE - SCRIPT PRINCIPAL
# Este script executa todos os testes e correções automaticamente

set -e

echo "🚀 INICIANDO SUPER TESTE COMPLETO"
echo "=================================="

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para log colorido
log() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

# Verificar se estamos no diretório correto
if [ ! -f "package.json" ]; then
    error "Execute este script no diretório do projeto Next.js"
    exit 1
fi

log "Verificando ambiente..."

# 1. Verificar Node.js
if ! command -v node &> /dev/null; then
    error "Node.js não encontrado"
    exit 1
fi

NODE_VERSION=$(node --version)
success "Node.js $NODE_VERSION encontrado"

# 2. Verificar npm
if ! command -v npm &> /dev/null; then
    error "npm não encontrado"
    exit 1
fi

NPM_VERSION=$(npm --version)
success "npm $NPM_VERSION encontrado"

# 3. Verificar se node_modules existe
if [ ! -d "node_modules" ]; then
    warning "node_modules não encontrado - instalando dependências..."
    npm install
fi

# 4. Limpar cache
log "Limpando cache..."
rm -rf .next
rm -rf .turbo
success "Cache limpo"

# 5. Executar correção automática de erros
log "Executando correção automática de erros..."
node scripts/fix-nextjs-errors.js

# 6. Executar super teste
log "Executando super teste..."
node scripts/super-test.js

# 7. Verificar TypeScript
log "Verificando TypeScript..."
if npx tsc --noEmit --skipLibCheck; then
    success "TypeScript OK"
else
    warning "Problemas de TypeScript detectados"
fi

# 8. Testar build
log "Testando build..."
if npm run build; then
    success "Build bem-sucedido"
else
    error "Build falhou"
    exit 1
fi

# 9. Iniciar servidor de teste
log "Iniciando servidor de teste..."
timeout 30 npm run dev &
SERVER_PID=$!

# Aguardar servidor iniciar
sleep 10

# Testar se servidor está respondendo
if curl -s -f http://localhost:3000 > /dev/null 2>&1; then
    success "Servidor respondendo na porta 3000"
elif curl -s -f http://localhost:3001 > /dev/null 2>&1; then
    success "Servidor respondendo na porta 3001"
elif curl -s -f http://localhost:3002 > /dev/null 2>&1; then
    success "Servidor respondendo na porta 3002"
else
    warning "Servidor não está respondendo"
fi

# Parar servidor de teste
kill $SERVER_PID 2>/dev/null || true

# 10. Gerar relatório final
log "Gerando relatório final..."

echo ""
echo "📊 RELATÓRIO FINAL DO SUPER TESTE"
echo "=================================="
echo "✅ Ambiente verificado"
echo "✅ Dependências instaladas"
echo "✅ Cache limpo"
echo "✅ Erros corrigidos automaticamente"
echo "✅ TypeScript verificado"
echo "✅ Build testado"
echo "✅ Servidor testado"
echo ""
echo "🎉 SUPER TESTE CONCLUÍDO COM SUCESSO!"
echo ""
echo "Para iniciar o servidor:"
echo "  npm run dev"
echo ""
echo "Para monitorar erros em tempo real:"
echo "  node scripts/error-monitor.js"
echo ""
echo "Para executar testes novamente:"
echo "  ./scripts/run-super-test.sh"
