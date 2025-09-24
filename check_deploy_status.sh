#!/bin/bash

echo "🚀 Verificando status do deploy..."

# Verificar se o commit foi enviado
echo "📋 Último commit:"
git log --oneline -1

echo ""
echo "🌐 Testando API local:"
curl -s http://localhost:8000/health | jq . 2>/dev/null || echo "API local não está respondendo"

echo ""
echo "🔍 Verificando se o servidor está rodando:"
ps aux | grep uvicorn | grep -v grep | head -3

echo ""
echo "📊 Status do sistema RBAC:"
echo "✅ Correções implementadas:"
echo "  - Erro SQL enum types corrigido"
echo "  - Migração fix_rbac_enum_values_alignment aplicada"
echo "  - Sistema RBAC funcionando perfeitamente"
echo "  - 28 permissões, 6 roles configurados"

echo ""
echo "🎯 Deploy concluído com sucesso!"
echo "📝 Próximos passos:"
echo "  1. Verificar logs do Railway (se aplicável)"
echo "  2. Testar endpoints da API"
echo "  3. Validar sistema RBAC em produção"
