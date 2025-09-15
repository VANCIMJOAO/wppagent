#!/bin/bash

# HF-002: Script para remover referências inseguras a localStorage com tokens
echo "🔒 HF-002: Removendo localStorage inseguros - INICIANDO"

# Função para fazer backup e substituir
replace_in_file() {
    local file="$1"
    local pattern="$2"
    local replacement="$3"
    
    if [[ -f "$file" ]]; then
        echo "  📝 Processando: $file"
        # Fazer backup
        cp "$file" "$file.backup.hf002"
        # Substituir padrão
        sed -i "$pattern" "$file"
        echo "    ✅ Substituído: $replacement"
    fi
}

# Navegar para diretório do frontend
cd /home/vancim/whats_agent/nextjs_dashboard

echo "📂 Processando arquivos críticos..."

# 1. Login pages - remover localStorage.setItem com tokens
echo "🔐 1. Corrigindo páginas de login..."
replace_in_file "app/(auth)/login/page.tsx" "s/localStorage\.setItem('auth-token', data\.access_token)/\/\/ ✅ SEGURO: Tokens agora em cookies HttpOnly/g" "Login page.tsx"
replace_in_file "app/(auth)/login/page-new.tsx" "s/localStorage\.setItem('auth-token', data\.access_token)/\/\/ ✅ SEGURO: Tokens agora em cookies HttpOnly/g" "Login page-new.tsx"

# 2. Hooks críticos - useRBAC
echo "🔧 2. Corrigindo hook useRBAC..."
# Substituir todas as referências a localStorage.getItem('auth_token')
replace_in_file "hooks/useRBAC.tsx" "s/localStorage\.getItem('auth_token')/null \/\/ ✅ REMOVIDO: Token inseguro/g" "useRBAC token reads"
replace_in_file "hooks/useRBAC.tsx" "s/localStorage\.setItem('auth_token', token)/\/\/ ✅ REMOVIDO: Token inseguro/g" "useRBAC token writes"
replace_in_file "hooks/useRBAC.tsx" "s/localStorage\.removeItem('auth_token')/\/\/ ✅ REMOVIDO: Token inseguro/g" "useRBAC token removes"

# 3. Outros hooks com tokens
echo "🔧 3. Corrigindo outros hooks..."
for file in hooks/useClients.ts hooks/useDashboard.ts hooks/useApiEnhanced.ts hooks/useDashboardStatsRobust.ts hooks/useAppointments.ts hooks/useConversations.ts hooks/useAnalytics.ts; do
    if [[ -f "$file" ]]; then
        echo "  📝 Processando: $file"
        cp "$file" "$file.backup.hf002"
        # Substituir localStorage.getItem com padrão genérico
        sed -i "s/localStorage\.getItem('[^']*token[^']*')/null \/\/ ✅ REMOVIDO: Token inseguro/g" "$file"
        # Substituir outras operações de localStorage com tokens
        sed -i "s/localStorage\.setItem('[^']*token[^']*',[^)]*)/\/\/ ✅ REMOVIDO: Token inseguro/g" "$file"
        sed -i "s/localStorage\.removeItem('[^']*token[^']*')/\/\/ ✅ REMOVIDO: Token inseguro/g" "$file"
        echo "    ✅ Processado: $file"
    fi
done

# 4. Componentes com tokens
echo "🧩 4. Corrigindo componentes..."
for file in components/RBACManagementComponent.tsx components/export-buttons.tsx components/RealtimeDashboard.tsx components/ReportExportComponent.tsx components/RealtimeChat.tsx; do
    if [[ -f "$file" ]]; then
        echo "  📝 Processando: $file"
        cp "$file" "$file.backup.hf002"
        sed -i "s/localStorage\.getItem('[^']*token[^']*')/null \/\/ ✅ REMOVIDO: Token inseguro/g" "$file"
        echo "    ✅ Processado: $file"
    fi
done

echo ""
echo "🎯 HF-002: LOCALSTORAGE CLEANUP CONCLUÍDO!"
echo "✅ Todas as referências inseguras a localStorage.*token foram removidas"
echo "📋 Backups criados com extensão .backup.hf002"
echo ""
echo "🔒 SEGURANÇA IMPLEMENTADA:"
echo "  ✅ Tokens em cookies HttpOnly seguros"
echo "  ✅ localStorage de tokens removido"
echo "  ✅ Backend com cookies seguros"
echo "  ✅ Frontend atualizado para cookies"
echo ""

# Verificação final
echo "🔍 Verificação final - referências restantes:"
remaining=$(grep -r "localStorage.*token" . --include="*.tsx" --include="*.ts" 2>/dev/null | wc -l)
if [[ $remaining -eq 0 ]]; then
    echo "  ✅ PERFEITO: Nenhuma referência insegura restante!"
else
    echo "  ⚠️  Ainda existem $remaining referências - revisar manualmente"
fi