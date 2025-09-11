#!/bin/bash

echo "🧹 LIMPEZA COMPLETA DO NEXTJS_DASHBOARD"
echo "========================================"

cd /home/vancim/whats_agent/nextjs_dashboard

# Arquivos de documentação desnecessários
echo "📝 Removendo arquivos de documentação..."
rm -f DASHBOARD_MONITORAMENTO_IMPLEMENTADO.md
rm -f ERROR_BOUNDARIES_IMPLEMENTATION.md
rm -f SECURITY-LOGS-REPORT.md
rm -f TYPESCRIPT-SAFETY-REPORT.md

# Arquivos de log e configuração temporária
echo "📄 Removendo logs e configs temporários..."
rm -f build.log
rm -f server.log
rm -f fix-config.json
rm -f .env.local.fixed
rm -f middleware.ts.backup

# Arquivos de teste JavaScript/debug
echo "🧪 Removendo arquivos de teste e debug..."
rm -f test-conversas-debug.js
rm -f test-corrected-api.js
rm -f test_monitoring_integration.js

# Backup files desnecessários
echo "💾 Removendo backups de páginas desnecessários..."
rm -f app/\(dashboard\)/conversas/page-backup-*.tsx
rm -f app/\(dashboard\)/conversas/page-backup.tsx
rm -f app/\(dashboard\)/conversas/page-corrected.tsx
rm -f app/\(dashboard\)/conversas/page-fixed.tsx
rm -f app/\(dashboard\)/conversas/page-new.tsx
rm -f app/\(dashboard\)/conversas/page-old-chat.tsx
rm -f app/\(dashboard\)/conversas/page-old.tsx
rm -f app/\(dashboard\)/conversas/page-whatsapp-fixed.tsx

# Pastas de teste
echo "🗂️ Removendo pastas de teste..."
rm -rf __tests__/
rm -rf e2e/
rm -rf tests/
rm -rf test-results/
rm -rf docs/

# Arquivos de build e cache temporários
echo "🔄 Removendo arquivos temporários de build..."
rm -f tsconfig.tsbuildinfo

# Componente duplicado
echo "🔧 Removendo componentes duplicados..."
if [ -f "components/auth/LoginForm.tsx" ]; then
    rm -f components/auth/LoginForm.tsx
fi

echo ""
echo "✅ LIMPEZA DO NEXTJS_DASHBOARD CONCLUÍDA!"
echo "========================================="
echo ""
echo "📋 ESTRUTURA MANTIDA (essencial):"
echo ""
echo "🔧 Configuração:"
echo "  - package.json, package-lock.json"
echo "  - next.config.js, tailwind.config.js"
echo "  - tsconfig.json, postcss.config.js"
echo "  - .env.example, .env.local, .gitignore"
echo "  - next-env.d.ts"
echo ""
echo "📱 Aplicação:"
echo "  - app/ (páginas e API routes)"
echo "  - components/ (componentes React)"
echo "  - hooks/ (custom hooks)"
echo "  - lib/ (utilitários)"
echo "  - contexts/ (React contexts)"
echo "  - types/ (TypeScript types)"
echo "  - styles/ (estilos CSS)"
echo "  - public/ (assets estáticos)"
echo ""
echo "🚀 Outros:"
echo "  - middleware.ts (Next.js middleware)"
echo "  - README.md (documentação do dashboard)"
echo "  - node_modules/, .next/, .swc/ (dependências e build)"
echo ""
echo "🎉 Next.js Dashboard limpo e organizado!"
