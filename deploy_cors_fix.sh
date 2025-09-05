#!/bin/bash

# 🚀 SCRIPT DE DEPLOY PARA CORREÇÃO DE CORS
# Este script faz deploy das alterações no Railway

echo "🔧 Iniciando deploy para correção de CORS..."

# Verificar se estamos no diretório correto
if [ ! -f "app/main.py" ]; then
    echo "❌ Erro: Execute este script na raiz do projeto"
    exit 1
fi

# Verificar alterações
echo "📝 Verificando alterações..."
git status

# Adicionar arquivos modificados
echo "➕ Adicionando arquivos..."
git add app/main.py
git add app/cors_config.py  
git add app/auth/middleware.py

# Fazer commit
echo "💾 Fazendo commit..."
git commit -m "🔧 Fix CORS: Configuração avançada para Railway

- Criado app/cors_config.py com configurações específicas do Railway
- Middleware de autenticação agora permite requests OPTIONS 
- Adicionados endpoints de teste /cors/test e /cors/debug
- Headers CORS mais específicos e configurações otimizadas
- Resolução do problema de preflight requests bloqueados"

# Push para o Railway
echo "🚀 Fazendo deploy no Railway..."
git push origin main

echo "✅ Deploy concluído!"
echo ""
echo "🧪 Para testar CORS após o deploy:"
echo "1. Aguarde alguns minutos para o deploy completar"
echo "2. Teste: https://wppagent-production.up.railway.app/cors/test"
echo "3. Debug: https://wppagent-production.up.railway.app/cors/debug"
echo "4. Console do navegador:"
echo "   fetch('https://wppagent-production.up.railway.app/cors/test')"
echo "   .then(r => r.json()).then(console.log)"
echo ""
echo "🔍 Monitorar logs no Railway para verificar se CORS está funcionando"
