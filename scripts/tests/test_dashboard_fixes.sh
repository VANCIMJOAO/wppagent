#!/bin/bash
# Teste rápido do dashboard após correções

echo "🧪 TESTE RÁPIDO - Dashboard Correções de Loop"
echo "============================================="

# Verificar se dashboard debug está rodando
echo "1. Verificando dashboard debug..."
if curl -s http://localhost:8051/ > /dev/null; then
    echo "✅ Dashboard debug funcionando em http://localhost:8051/"
else
    echo "❌ Dashboard debug não está funcionando"
fi

# Verificar dashboard principal
echo "2. Verificando dashboard principal..."
if curl -s http://localhost:8050/ > /dev/null; then
    echo "✅ Dashboard principal acessível em http://localhost:8050/"
else
    echo "❌ Dashboard principal não está acessível"
fi

echo ""
echo "🎯 TESTES RECOMENDADOS:"
echo "1. Acesse: http://localhost:8051/ (Debug - sem rate limiting)"
echo "2. Teste login com: admin / admin123"
echo "3. Verifique se não há loops nos logs"
echo "4. Se funcionar, teste: http://localhost:8050/ (Principal)"
echo ""
echo "🔍 PONTOS DE VERIFICAÇÃO:"
echo "[ ] Login funciona sem loops"
echo "[ ] Dashboard carrega após login"
echo "[ ] Navegação entre páginas funciona"
echo "[ ] Logs não mostram callbacks excessivos"
echo "[ ] Rate limiting não bloqueia uso normal"

# Mostrar processos Python rodando
echo ""
echo "📊 Processos dashboard ativos:"
ps aux | grep -E "(dashboard|python)" | grep -v grep | head -5

echo ""
echo "🚀 Teste concluído!"
