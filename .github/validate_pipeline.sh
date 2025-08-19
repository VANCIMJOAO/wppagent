#!/bin/bash
# 🔧 Script de Validação do Pipeline CI/CD

echo "🔍 VALIDANDO CORREÇÕES DO PIPELINE CI/CD..."

# Cores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PIPELINE_FILE=".github/workflows/ci-cd.yml"

if [ ! -f "$PIPELINE_FILE" ]; then
    echo -e "${RED}❌ Arquivo $PIPELINE_FILE não encontrado!${NC}"
    exit 1
fi

echo -e "${BLUE}📁 Validando arquivo: $PIPELINE_FILE${NC}"

# Função para verificar correções
check_correction() {
    local description="$1"
    local search_pattern="$2"
    local expected_count="$3"
    
    local count=$(grep -c "$search_pattern" "$PIPELINE_FILE")
    
    if [ "$count" -eq "$expected_count" ]; then
        echo -e "${GREEN}✅ $description${NC}"
        return 0
    else
        echo -e "${RED}❌ $description (encontrado: $count, esperado: $expected_count)${NC}"
        return 1
    fi
}

echo ""
echo "🔧 VERIFICANDO CORREÇÕES APLICADAS:"
echo "================================="

# Verificações das correções
ERRORS=0

# 1. Trivy action corrigida
if ! check_correction "Trivy action atualizada" "aquasecurity/trivy-action@master" 1; then
    ((ERRORS++))
fi

# 2. Timeouts adicionados
if ! check_correction "Timeout no job test" "timeout-minutes: 15" 1; then
    ((ERRORS++))
fi

if ! check_correction "Timeout no job build" "timeout-minutes: 30" 1; then
    ((ERRORS++))
fi

# 3. Deploy staging condition corrigida
if ! check_correction "Deploy staging condition" "github.event_name == 'push'" 2; then
    ((ERRORS++))
fi

# 4. Health check condition corrigida
if ! check_correction "Health check condition melhorada" "always()" 1; then
    # Verificação alternativa - procurar por "always() &&"
    always_count=$(grep -c "always() &&" "$PIPELINE_FILE")
    if [ "$always_count" -eq 1 ]; then
        echo -e "${GREEN}✅ Health check condition melhorada (formato alternativo)${NC}"
    else
        ((ERRORS++))
    fi
fi

# 5. GitHub release action atualizada
if ! check_correction "GitHub release action atualizada" "softprops/action-gh-release@v1" 1; then
    ((ERRORS++))
fi

# 6. Variables usage
if ! check_correction "Variables configuradas" '\${{ vars\.' 2; then
    ((ERRORS++))
fi

echo ""
echo "🧪 VERIFICAÇÕES SINTÁTICAS:"
echo "=========================="

# Verificar se yamllint está disponível
if command -v yamllint &> /dev/null; then
    echo -e "${BLUE}📋 Executando yamllint...${NC}"
    if yamllint "$PIPELINE_FILE" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ YAML syntax válida${NC}"
    else
        echo -e "${RED}❌ YAML syntax inválida${NC}"
        yamllint "$PIPELINE_FILE"
        ((ERRORS++))
    fi
else
    echo -e "${YELLOW}⚠️ yamllint não encontrado, instalando...${NC}"
    pip install yamllint >/dev/null 2>&1
    if yamllint "$PIPELINE_FILE" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ YAML syntax válida${NC}"
    else
        echo -e "${RED}❌ YAML syntax inválida${NC}"
        ((ERRORS++))
    fi
fi

echo ""
echo "📊 VERIFICAÇÃO DE JOBS:"
echo "======================"

# Verificar se jobs essenciais existem
JOBS=("test" "security" "build" "deploy-staging" "health-check" "deploy-production" "release" "cleanup")

for job in "${JOBS[@]}"; do
    if grep -q "^  $job:" "$PIPELINE_FILE"; then
        echo -e "${GREEN}✅ Job '$job' encontrado${NC}"
    else
        echo -e "${RED}❌ Job '$job' não encontrado${NC}"
        ((ERRORS++))
    fi
done

echo ""
echo "🎯 RESULTADO FINAL:"
echo "=================="

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}🎉 PIPELINE 100% CORRIGIDO E VALIDADO!${NC}"
    echo ""
    echo -e "${BLUE}📋 Próximos passos:${NC}"
    echo "1. Configure as variables no GitHub:"
    echo "   - STAGING_URL = https://staging.whatsapp-agent.com"
    echo "   - PRODUCTION_URL = https://wppagent-production.up.railway.app"
    echo ""
    echo "2. Se repositório privado, configure:"
    echo "   - CODECOV_TOKEN = seu_token_codecov"
    echo ""
    echo "3. Commit e push para testar o pipeline"
    echo ""
    echo -e "${GREEN}✅ Pipeline pronto para uso em produção!${NC}"
else
    echo -e "${RED}❌ ENCONTRADOS $ERRORS ERROS NO PIPELINE${NC}"
    echo ""
    echo -e "${YELLOW}🔧 Corrija os erros acima antes de usar o pipeline${NC}"
    exit 1
fi