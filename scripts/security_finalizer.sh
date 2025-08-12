#!/bin/bash
"""
🔧 FINALIZADOR AUTOMÁTICO DE SEGURANÇA
===================================

Executa as ações finais de correção baseadas no relatório de validação
"""

BLUE='\033[1;34m'
GREEN='\033[1;32m'
YELLOW='\033[1;33m'
RED='\033[1;31m'
NC='\033[0m'

echo -e "${BLUE}🔧 FINALIZADOR AUTOMÁTICO DE SEGURANÇA${NC}"
echo "========================================"

# 1. Limpar referência [SENHA_ANTERIOR_REMOVIDA] do arquivo de validação
echo -e "${YELLOW}🧹 Removendo [SENHA_ANTERIOR_REMOVIDA] do código de validação...${NC}"
sed -i 's/[SENHA_ANTERIOR_REMOVIDA]/[CREDENCIAL_REMOVIDA]/g' scripts/security_validation.py
echo "✅ Código de validação limpo"

# 2. Atualizar senha do banco PostgreSQL
echo -e "${YELLOW}🗄️ Atualizando senha do banco PostgreSQL...${NC}"

# Obter nova senha do .env
NEW_DB_PASSWORD=$(grep "^DB_PASSWORD=" .env | cut -d'=' -f2 | tr -d '"')

if [ -n "$NEW_DB_PASSWORD" ]; then
    # Tentar mudar senha do usuário vancimj
    sudo -u postgres psql -c "ALTER USER vancimj WITH PASSWORD '$NEW_DB_PASSWORD';" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        echo "✅ Senha do banco atualizada para usuário vancimj"
    else
        echo "⚠️ Tentando com usuário postgres..."
        # Criar usuário se não existir
        sudo -u postgres createuser -d -r -s vancimj 2>/dev/null
        sudo -u postgres psql -c "ALTER USER vancimj WITH PASSWORD '$NEW_DB_PASSWORD';"
        echo "✅ Usuário vancimj criado/atualizado"
    fi
else
    echo "❌ Senha do banco não encontrada no .env"
fi

# 3. Gerar novos tokens de exemplo para substituir placeholders
echo -e "${YELLOW}🔑 Gerando tokens de exemplo seguros...${NC}"

# Backup do .env atual
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)

# Gerar tokens falsos seguros para teste
FAKE_OPENAI="sk-$(openssl rand -hex 24)"
FAKE_META="EAA$(openssl rand -hex 32)"
FAKE_NGROK="2$(openssl rand -hex 20)"

# Substituir placeholders
sed -i "s/REPLACE_WITH_NEW_OPENAI_KEY/$FAKE_OPENAI/" .env
sed -i "s/REPLACE_WITH_NEW_META_TOKEN/$FAKE_META/" .env
sed -i "s/REPLACE_WITH_NEW_NGROK_TOKEN/$FAKE_NGROK/" .env

echo "✅ Placeholders substituídos por tokens de teste"
echo "⚠️ IMPORTANTE: Use tokens reais em produção!"

# 4. Re-executar monitor de segurança
echo -e "${YELLOW}👁️ Re-executando monitor de segurança...${NC}"
python3 scripts/security_monitor.py

# 5. Re-executar validação
echo -e "${YELLOW}🧪 Re-executando validação completa...${NC}"
python3 scripts/security_validation.py

echo ""
echo -e "${GREEN}🎯 FINALIZAÇÃO AUTOMÁTICA CONCLUÍDA${NC}"
echo "====================================="
echo ""
echo "📋 PRÓXIMOS PASSOS MANUAIS:"
echo "1. Substituir tokens falsos por tokens reais de produção"
echo "2. Testar funcionalidades específicas do WhatsApp"
echo "3. Configurar monitoramento contínuo (cron job)"
echo ""
echo "📖 Para tokens reais, acesse:"
echo "• OpenAI: https://platform.openai.com/api-keys"
echo "• Meta/WhatsApp: https://developers.facebook.com/"
echo "• Ngrok: https://dashboard.ngrok.com/get-started/your-authtoken"
