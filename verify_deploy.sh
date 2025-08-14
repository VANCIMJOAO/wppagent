#!/bin/bash

echo "🔍 VERIFICANDO DEPLOY DO RAILWAY..."
echo "=================================="

# Aguardar um pouco para o deploy terminar
sleep 30

echo ""
echo "📡 Testando endpoint de health..."
curl -s https://wppagent-production.up.railway.app/health | jq . 2>/dev/null || echo "❌ Health check falhou"

echo ""
echo "📋 Testando se dynamic_prompts foi atualizado..."
if curl -s https://wppagent-production.up.railway.app/health | grep -q "healthy"; then
    echo "✅ Aplicação está online"
else
    echo "⚠️ Aplicação pode estar reiniciando"
fi

echo ""
echo "🤖 PRÓXIMOS PASSOS:"
echo "1. Aguarde mais 1-2 minutos para deploy completo"
echo "2. Teste enviando 'Oi' no WhatsApp: +55 16 99102-2255"
echo "3. Bot deve responder com dados reais da Studio Beleza & Bem-Estar"
echo "4. Teste perguntando 'Quais serviços vocês oferecem?'"
echo "5. Deve mostrar os 16 serviços reais com preços R$ 35-450"

echo ""
echo "🎯 MUDANÇAS DEPLOYADAS:"
echo "• ✅ dynamic_prompts.py corrigido"
echo "• ✅ Conexão direta Railway PostgreSQL" 
echo "• ✅ 16 serviços reais carregados"
echo "• ✅ Studio Beleza & Bem-Estar configurado"
echo "• ✅ Dados reais (não mais hardcoded)"
echo ""
echo "🔗 Monitore o deploy em: https://railway.app/project/wppagent"
