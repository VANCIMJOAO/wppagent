#!/bin/bash
# Script de teste para configuração de produção com o token OpenAI real

# Seu token OpenAI real
OPENAI_TOKEN="sk-your-openai-key-here"

echo "🔑 CONFIGURAÇÃO RÁPIDA COM TOKEN REAL"
echo "===================================="
echo ""

# Criar backup do .env
echo "📋 Fazendo backup do .env..."
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)

# Obter token atual do .env
current_openai=$(grep "^OPENAI_API_KEY=" .env | cut -d'=' -f2 | tr -d '"')

echo "🔄 Substituindo token OpenAI..."
echo "  Atual: ${current_openai:0:20}..."
echo "  Novo:  ${OPENAI_TOKEN:0:20}..."

# Substituir token
sed -i "s|OPENAI_API_KEY=\"$current_openai\"|OPENAI_API_KEY=\"$OPENAI_TOKEN\"|" .env

echo "✅ Token OpenAI atualizado!"
echo ""

echo "🧪 Executando validação com token real..."
python3 scripts/security_validation.py

echo ""
echo "🎉 CONFIGURAÇÃO CONCLUÍDA!"
echo "  💡 Para tokens Meta e Ngrok, obtenha-os nos respectivos painéis"
echo "  📱 Meta: https://developers.facebook.com/"
echo "  🌐 Ngrok: https://dashboard.ngrok.com/get-started/your-authtoken"
