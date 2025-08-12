#!/bin/bash

# 🚀 Script de Push para Repositório Git
# Execute este script após configurar o remote do seu repositório

echo "🚀 Preparando push do WhatsApp Agent v2.0 para repositório Git..."
echo "=================================================="

# Verificar se há remote configurado
if ! git remote get-url origin >/dev/null 2>&1; then
    echo "❌ Nenhum remote 'origin' configurado!"
    echo ""
    echo "📋 Para configurar o remote, execute:"
    echo "git remote add origin https://github.com/SEU_USUARIO/whatsapp-agent.git"
    echo ""
    echo "🔑 Ou se for repositório privado:"
    echo "git remote add origin git@github.com:SEU_USUARIO/whatsapp-agent.git"
    echo ""
    echo "📚 Depois execute novamente este script"
    exit 1
fi

echo "✅ Remote configurado:"
git remote -v

echo ""
echo "📊 Status atual:"
git status --porcelain

echo ""
echo "📋 Últimos commits:"
git log --oneline -n 5

echo ""
echo "🏷️ Tags:"
git tag -l

echo ""
echo "🚀 Fazendo push dos commits..."
git push origin master

echo ""
echo "🏷️ Fazendo push das tags..."
git push origin --tags

echo ""
echo "✅ Push concluído com sucesso!"
echo ""
echo "🌐 Agora você pode acessar seu repositório e:"
echo "   - Criar release notes no GitHub"
echo "   - Configurar Actions/CI-CD"
echo "   - Documentar o projeto"
echo ""
echo "🎯 Próximo passo: Deploy em produção!"
echo "   ./scripts/deployment/deploy_production.sh"
