#!/bin/bash
# Script de teste para verificar o funcionamento do dashboard

echo "🧪 TESTE - Verificando Dashboard WhatsApp Agent"
echo "=============================================="

# Verificar se o dashboard está rodando
echo "1. Verificando se o dashboard está acessível..."
if curl -s http://localhost:8050/ > /dev/null; then
    echo "✅ Dashboard acessível em http://localhost:8050/"
else
    echo "❌ Dashboard não está acessível"
    exit 1
fi

# Verificar se a página de login carrega
echo "2. Verificando página de login..."
if curl -s http://localhost:8050/ | grep -q "WhatsApp Agent"; then
    echo "✅ Página de login carregando corretamente"
else
    echo "❌ Problema na página de login"
fi

# Verificar se os containers estão saudáveis
echo "3. Verificando status dos containers..."
cd /home/vancim/whats_agent
docker-compose ps

echo ""
echo "🎯 INSTRUÇÕES DE TESTE:"
echo "1. Acesse: http://localhost:8050/"
echo "2. Use as credenciais:"
echo "   - Usuário: admin"
echo "   - Senha: admin123"
echo "3. Verifique se o login funciona sem loops"
echo ""
echo "📋 CHECKLIST DE TESTE:"
echo "[ ] Dashboard carrega sem erros"
echo "[ ] Página de login aparece"
echo "[ ] Login com admin/admin123 funciona"
echo "[ ] Redirecionamento para dashboard após login"
echo "[ ] Não há loops infinitos nos logs"
echo "[ ] Navegação entre páginas funciona"
echo ""
echo "🚀 Teste concluído!"
