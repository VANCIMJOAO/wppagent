#!/bin/bash
# Script de limpeza adicional da raiz do projeto WhatsApp Agent
# Data: $(date +%Y-%m-%d)

echo "🧹 INICIANDO LIMPEZA ADICIONAL DA RAIZ DO PROJETO"
echo "================================================="

# Criar diretório de backup para logs da limpeza
CLEANUP_LOG_DIR="logs/cleanup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$CLEANUP_LOG_DIR"

echo "📝 Logs serão salvos em: $CLEANUP_LOG_DIR"

# 1. REMOVER ARQUIVOS TEMPORÁRIOS E VAZIOS
echo ""
echo "🗑️  1. REMOVENDO ARQUIVOS VAZIOS E TEMPORÁRIOS..."

# Arquivo com nome estranho (parece ser output de comando psql mal redirecionado)
if [ -f "ql -h localhost -p 5432 -U vancimj -d whats_agent -c \d users" ]; then
    mv "ql -h localhost -p 5432 -U vancimj -d whats_agent -c \d users" "$CLEANUP_LOG_DIR/db_output_temp.txt"
    echo "✅ Removido arquivo com nome de comando psql"
fi

# Arquivos MD vazios (documentos de status que não têm conteúdo)
EMPTY_MD_FILES=(
    "AUTHENTICATION_SUCCESS.md"
    "CLEANUP_ANALYSIS.md" 
    "IMPLEMENTACAO_RATE_LIMITING_COMPLETA.md"
    "SISTEMA_FUNCIONANDO.md"
    "SISTEMA_IMPLEMENTADO.md"
    "TESTES_REAIS_CONCLUIDOS.md"
)

for file in "${EMPTY_MD_FILES[@]}"; do
    if [ -f "$file" ] && [ ! -s "$file" ]; then
        mv "$file" "$CLEANUP_LOG_DIR/"
        echo "✅ Removido: $file (arquivo vazio)"
    fi
done

# Arquivos Python de teste vazios
EMPTY_TEST_FILES=(
    "test_notification.py"
    "test_production.py"
    "validate_production.py"
)

for file in "${EMPTY_TEST_FILES[@]}"; do
    if [ -f "$file" ] && [ ! -s "$file" ]; then
        mv "$file" "$CLEANUP_LOG_DIR/"
        echo "✅ Removido: $file (teste vazio)"
    fi
done

# 2. ORGANIZAR DOCUMENTAÇÃO
echo ""
echo "📚 2. ORGANIZANDO DOCUMENTAÇÃO..."

# Mover documentos importantes para docs/
if [ -f "DATABASE_OPTIMIZATION_COMPLETE.md" ]; then
    mv "DATABASE_OPTIMIZATION_COMPLETE.md" "docs/"
    echo "✅ Movido DATABASE_OPTIMIZATION_COMPLETE.md para docs/"
fi

if [ -f "WHATSAPP_INTEGRATION_IMPROVEMENTS.md" ]; then
    mv "WHATSAPP_INTEGRATION_IMPROVEMENTS.md" "docs/"
    echo "✅ Movido WHATSAPP_INTEGRATION_IMPROVEMENTS.md para docs/"
fi

# 3. VERIFICAR E LIMPAR DOCKERFILES VAZIOS
echo ""
echo "🐳 3. VERIFICANDO DOCKERFILES..."

if [ -f "Dockerfile" ] && [ ! -s "Dockerfile" ]; then
    mv "Dockerfile" "$CLEANUP_LOG_DIR/"
    echo "✅ Removido Dockerfile vazio"
fi

if [ -f "Dockerfile.streamlit" ] && [ ! -s "Dockerfile.streamlit" ]; then
    mv "Dockerfile.streamlit" "$CLEANUP_LOG_DIR/"
    echo "✅ Removido Dockerfile.streamlit vazio"
fi

if [ -f "docker-compose.yml" ] && [ ! -s "docker-compose.yml" ]; then
    mv "docker-compose.yml" "$CLEANUP_LOG_DIR/"
    echo "✅ Removido docker-compose.yml vazio"
fi

# 4. ORGANIZAR SCRIPTS E TESTES
echo ""
echo "🔧 4. ORGANIZANDO SCRIPTS E TESTES..."

# Mover test_whatsapp_integration.py para tests/ se não vazio
if [ -f "test_whatsapp_integration.py" ] && [ -s "test_whatsapp_integration.py" ]; then
    mv "test_whatsapp_integration.py" "tests/"
    echo "✅ Movido test_whatsapp_integration.py para tests/"
fi

# Verificar dashboard_whatsapp_complete.py
if [ -f "dashboard_whatsapp_complete.py" ]; then
    SIZE=$(wc -c < "dashboard_whatsapp_complete.py")
    if [ $SIZE -gt 1000 ]; then
        echo "📊 dashboard_whatsapp_complete.py mantido ($(echo "scale=1; $SIZE/1024" | bc)KB)"
    else
        mv "dashboard_whatsapp_complete.py" "$CLEANUP_LOG_DIR/"
        echo "✅ Removido dashboard_whatsapp_complete.py (muito pequeno)"
    fi
fi

# 5. LIMPEZA DE CACHE E ARQUIVOS TEMPORÁRIOS
echo ""
echo "🧽 5. LIMPEZA DE CACHE..."

# Limpar cache do pytest
if [ -d ".pytest_cache" ]; then
    rm -rf ".pytest_cache"
    echo "✅ Cache do pytest removido"
fi

# Limpar arquivos .pyc se existirem na raiz
find . -maxdepth 1 -name "*.pyc" -delete 2>/dev/null && echo "✅ Arquivos .pyc removidos"

# 6. VERIFICAR PERMISSÕES DOS SCRIPTS
echo ""
echo "🔐 6. VERIFICANDO PERMISSÕES..."

SCRIPT_FILES=(
    "cleanup_project.sh"
    "run_dev.sh"
    "run_real_tests.sh"
    "setup_production.sh"
    "manage.py"
)

for script in "${SCRIPT_FILES[@]}"; do
    if [ -f "$script" ]; then
        chmod +x "$script"
        echo "✅ Permissões ajustadas: $script"
    fi
done

# 7. RELATÓRIO FINAL
echo ""
echo "📊 7. RELATÓRIO DA LIMPEZA"
echo "=========================="

echo "📁 Estrutura da raiz após limpeza:"
ls -la | grep -E '^-' | wc -l | xargs echo "Arquivos na raiz:"
ls -la | grep -E '^d' | wc -l | xargs echo "Diretórios na raiz:"

echo ""
echo "📋 Arquivos principais mantidos:"
ls -la *.py *.md *.toml *.ini *.txt *.sh 2>/dev/null | grep -v "^total" || echo "Nenhum arquivo principal encontrado"

echo ""
echo "🗂️  Arquivos movidos para backup: $CLEANUP_LOG_DIR"
ls -la "$CLEANUP_LOG_DIR/" 2>/dev/null | grep -v "^total" || echo "Nenhum arquivo movido"

echo ""
echo "✅ LIMPEZA ADICIONAL CONCLUÍDA COM SUCESSO!"
echo "🎯 Projeto mais organizado e limpo!"
