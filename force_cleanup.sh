#!/bin/bash
# Script para limpeza forçada quando arquivos "voltam"

echo "🧹 Iniciando limpeza forçada..."

# 1. Reset de qualquer mudança staged
echo "📦 Fazendo reset do Git..."
git reset HEAD . 2>/dev/null || true

# 2. Limpar caches do sistema
echo "🗂️ Limpando caches do sistema..."
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "*.tmp" -delete 2>/dev/null || true
find . -name "*.cache" -delete 2>/dev/null || true

# 3. Limpar caches do VS Code
echo "💾 Limpando caches do VS Code..."
rm -rf .vscode/settings.json 2>/dev/null || true

# 4. Remover arquivos vazios
echo "📄 Removendo arquivos vazios..."
find . -type f -empty -not -path "./.git/*" -delete 2>/dev/null || true

# 5. Remover diretórios vazios (exceto .git)
echo "📁 Removendo diretórios vazios..."
find . -type d -empty -not -path "./.git*" -delete 2>/dev/null || true

# 6. Verificar e remover pastas específicas se existirem
DIRS_TO_REMOVE=("scripts" "migrations" "frontend_examples" "tests")

for dir in "${DIRS_TO_REMOVE[@]}"; do
    if [ -d "$dir" ]; then
        echo "🗑️ Removendo pasta: $dir"
        rm -rf "$dir"
    fi
done

# 7. Commit automático das remoções
echo "💫 Fazendo commit das remoções..."
git add .
git status --porcelain | grep -E "^D " && {
    git commit -m "🗑️ LIMPEZA FORÇADA: Remoção definitiva de arquivos/pastas vazias"
    echo "✅ Commit realizado com sucesso!"
} || {
    echo "ℹ️ Nenhuma remoção para committar"
}

echo "🎉 Limpeza forçada concluída!"
echo ""
echo "📋 Para prevenir recriação automática:"
echo "   1. Feche e reabra o VS Code"
echo "   2. Use este script sempre que arquivos 'voltarem'"
echo "   3. Verifique extensões do VS Code que podem estar causando isso"
