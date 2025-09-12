#!/bin/bash
# 🧹 Script de Limpeza Completa - Remove arquivos vazios e caches
# Data: 12 de setembro de 2025
# Projeto: WhatsApp Agent

echo "🧹 Iniciando limpeza completa do projeto..."
echo "=" * 50

# Navegar para o diretório do projeto
cd /home/vancim/whats_agent

echo "🗑️ Removendo arquivos vazios (0 bytes)..."

# Encontrar e remover todos os arquivos vazios, excluindo diretórios importantes
find . -type f -size 0 \
    -not -path "./.git/*" \
    -not -path "./__pycache__/*" \
    -not -path "./.venv/*" \
    -not -path "./nextjs_dashboard/node_modules/*" \
    -not -path "*/logs/*" \
    -not -path "./.pytest_cache/*" \
    -exec rm -f {} \;

echo "✅ Arquivos vazios removidos!"

echo "🧽 Limpando caches Python..."
# Remover cache Python
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name "*.pyo" -delete 2>/dev/null || true
find . -name "*.pyd" -delete 2>/dev/null || true

echo "🧽 Limpando cache pytest..."
rm -rf .pytest_cache 2>/dev/null || true

echo "🧽 Limpando cache TypeScript/Node..."
rm -rf nextjs_dashboard/node_modules/.cache 2>/dev/null || true
rm -rf nextjs_dashboard/.next 2>/dev/null || true
rm -rf nextjs_dashboard/dist 2>/dev/null || true
rm -rf nextjs_dashboard/build 2>/dev/null || true

echo "🧽 Limpando arquivos temporários..."
rm -rf temp_files/* 2>/dev/null || true
rm -rf temp_reports/* 2>/dev/null || true
find . -name "*.tmp" -delete 2>/dev/null || true
find . -name "*.temp" -delete 2>/dev/null || true
find . -name ".DS_Store" -delete 2>/dev/null || true

echo "🧽 Limpando logs vazios..."
find logs/ -type f -size 0 -delete 2>/dev/null || true

echo "📊 Verificando resultado da limpeza..."
echo "Arquivos vazios restantes:"
EMPTY_FILES=$(find . -type f -size 0 \
    -not -path "./.git/*" \
    -not -path "./__pycache__/*" \
    -not -path "./.venv/*" \
    -not -path "./nextjs_dashboard/node_modules/*" \
    -not -path "*/logs/*" | wc -l)

if [ "$EMPTY_FILES" -eq 0 ]; then
    echo "✅ Nenhum arquivo vazio encontrado - Limpeza completa!"
else
    echo "⚠️  Ainda existem $EMPTY_FILES arquivos vazios"
    find . -type f -size 0 \
        -not -path "./.git/*" \
        -not -path "./__pycache__/*" \
        -not -path "./.venv/*" \
        -not -path "./nextjs_dashboard/node_modules/*" \
        -not -path "*/logs/*" | head -10
fi

echo ""
echo "🏁 Limpeza concluída!"
echo "📂 Estrutura do projeto:"
ls -la | grep "^d" | awk '{print "  • " $9}' | grep -v "^\.$\|^\.\.$"

echo ""
echo "📄 Arquivos na raiz:"
ls -la | grep "^-" | wc -l | awk '{print "  Total: " $1 " arquivos"}'

echo ""
echo "✅ Projeto limpo e organizado!"
