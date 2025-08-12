#!/bin/bash
# 🔑 CONFIGURADOR DE TOKENS DE PRODUÇÃO
# ==================================
# 
# Script interativo para substituir tokens de teste por tokens reais

# Cores para output
BLUE='\033[1;34m'
GREEN='\033[1;32m'
YELLOW='\033[1;33m'
RED='\033[1;31m'
CYAN='\033[1;36m'
NC='\033[0m'

echo -e "${BLUE}🔑 CONFIGURADOR DE TOKENS DE PRODUÇÃO${NC}"
echo "===================================="
echo ""
echo -e "${YELLOW}Este script irá substituir os tokens de teste por tokens reais de produção.${NC}"
echo -e "${YELLOW}Certifique-se de ter os tokens reais disponíveis antes de continuar.${NC}"
echo ""

# Backup do .env atual
echo -e "${CYAN}📋 Criando backup do .env atual...${NC}"
cp .env .env.backup.production.$(date +%Y%m%d_%H%M%S)
echo "✅ Backup criado"
echo ""

# Função para validar tokens
validate_openai_token() {
    local token="$1"
    # Novo formato: sk-proj-... ou sk-... com 100+ caracteres
    if [[ $token =~ ^sk-(proj-)?[a-zA-Z0-9_-]{90,}$ ]]; then
        return 0
    else
        return 1
    fi
}

validate_meta_token() {
    local token="$1"
    if [[ $token =~ ^EAA[a-zA-Z0-9]{50,}$ ]]; then
        return 0
    else
        return 1
    fi
}

validate_ngrok_token() {
    local token="$1"
    if [[ ${#token} -ge 20 ]]; then
        return 0
    else
        return 1
    fi
}

# 1. OpenAI Token
echo -e "${CYAN}🤖 CONFIGURAÇÃO DO TOKEN OPENAI${NC}"
echo "Acesse: https://platform.openai.com/api-keys"
echo "Crie uma nova API key e cole aqui:"
echo ""
while true; do
    read -p "OpenAI API Key (sk-...): " openai_token
    
    if [ -z "$openai_token" ]; then
        echo -e "${RED}❌ Token não pode estar vazio${NC}"
        continue
    fi
    
    if validate_openai_token "$openai_token"; then
        echo -e "${GREEN}✅ Token OpenAI válido${NC}"
        break
    else
        echo -e "${RED}❌ Formato de token OpenAI inválido (deve começar com 'sk-' ou 'sk-proj-' e ter 90+ caracteres)${NC}"
        echo "Exemplo: sk-proj-A07zujMDlqoU24lEP62wF_dvhmILphXdR5lUvjCrxl7G1nLrogP3zZHD7E..."
        continue
    fi
done
echo ""

# 2. Meta Token
echo -e "${CYAN}📱 CONFIGURAÇÃO DO TOKEN META/WHATSAPP${NC}"
echo "Acesse: https://developers.facebook.com/"
echo "Vá para seu app > WhatsApp > Configuração > Token de acesso"
echo ""
while true; do
    read -p "Meta Access Token (EAA...): " meta_token
    
    if [ -z "$meta_token" ]; then
        echo -e "${RED}❌ Token não pode estar vazio${NC}"
        continue
    fi
    
    if validate_meta_token "$meta_token"; then
        echo -e "${GREEN}✅ Token Meta válido${NC}"
        break
    else
        echo -e "${RED}❌ Formato de token Meta inválido (deve começar com 'EAA' e ter 50+ caracteres)${NC}"
        echo "Exemplo: EAA1234567890abcdef1234567890abcdef1234567890abcdef"
        continue
    fi
done
echo ""

# 3. Ngrok Token
echo -e "${CYAN}🌐 CONFIGURAÇÃO DO TOKEN NGROK${NC}"
echo "Acesse: https://dashboard.ngrok.com/get-started/your-authtoken"
echo "Copie seu authtoken e cole aqui:"
echo ""
while true; do
    read -p "Ngrok Auth Token: " ngrok_token
    
    if [ -z "$ngrok_token" ]; then
        echo -e "${RED}❌ Token não pode estar vazio${NC}"
        continue
    fi
    
    if validate_ngrok_token "$ngrok_token"; then
        echo -e "${GREEN}✅ Token Ngrok válido${NC}"
        break
    else
        echo -e "${RED}❌ Token Ngrok muito curto (deve ter pelo menos 20 caracteres)${NC}"
        continue
    fi
done
echo ""

# 4. Configuração opcional do Phone Number ID
echo -e "${CYAN}📞 CONFIGURAÇÃO DO PHONE NUMBER ID (Opcional)${NC}"
echo "Se você tem um Phone Number ID específico do WhatsApp Business:"
read -p "Phone Number ID (deixe vazio se não souber): " phone_number_id
echo ""

# Confirmar alterações
echo -e "${YELLOW}📋 RESUMO DAS CONFIGURAÇÕES:${NC}"
echo "OpenAI Token: ${openai_token:0:20}..."
echo "Meta Token: ${meta_token:0:20}..."
echo "Ngrok Token: ${ngrok_token:0:20}..."
if [ -n "$phone_number_id" ]; then
    echo "Phone Number ID: $phone_number_id"
fi
echo ""

read -p "Confirma as configurações acima? (s/N): " confirm
if [[ ! $confirm =~ ^[Ss]$ ]]; then
    echo "❌ Configuração cancelada"
    exit 1
fi

# Aplicar alterações
echo -e "${CYAN}🔧 Aplicando configurações...${NC}"

# Obter tokens atuais do .env para substituição
current_openai=$(grep "^OPENAI_API_KEY=" .env | cut -d'=' -f2 | tr -d '"')
current_meta=$(grep "^META_ACCESS_TOKEN=" .env | cut -d'=' -f2 | tr -d '"')
current_ngrok=$(grep "^NGROK_AUTHTOKEN=" .env | cut -d'=' -f2 | tr -d '"')

# Substituir tokens
sed -i "s|OPENAI_API_KEY=\"$current_openai\"|OPENAI_API_KEY=\"$openai_token\"|" .env
sed -i "s|META_ACCESS_TOKEN=\"$current_meta\"|META_ACCESS_TOKEN=\"$meta_token\"|" .env
sed -i "s|NGROK_AUTHTOKEN=\"$current_ngrok\"|NGROK_AUTHTOKEN=\"$ngrok_token\"|" .env

# Configurar Phone Number ID se fornecido
if [ -n "$phone_number_id" ]; then
    if grep -q "^PHONE_NUMBER_ID=" .env; then
        sed -i "s|PHONE_NUMBER_ID=.*|PHONE_NUMBER_ID=\"$phone_number_id\"|" .env
    else
        echo "PHONE_NUMBER_ID=\"$phone_number_id\"" >> .env
    fi
fi

echo "✅ Tokens de produção configurados"
echo ""

# Validar configurações
echo -e "${CYAN}🧪 Executando validação com tokens reais...${NC}"
python3 scripts/security_validation.py

echo ""
echo -e "${GREEN}🎉 CONFIGURAÇÃO DE PRODUÇÃO CONCLUÍDA!${NC}"
echo "=================================="
echo ""
echo -e "${CYAN}📋 PRÓXIMOS PASSOS:${NC}"
echo "1. Verificar se a validação passou sem erros"
echo "2. Testar funcionalidades específicas do seu app"
echo "3. Configurar monitoramento contínuo:"
echo "   crontab -e"
echo "   # Adicionar: 0 */6 * * * cd $(pwd) && python3 scripts/security_monitor.py"
echo ""
echo -e "${YELLOW}⚠️ IMPORTANTE:${NC}"
echo "- Nunca compartilhe os tokens reais"
echo "- Configure rotação automática dos tokens"
echo "- Monitore regularmente os logs de segurança"
echo ""
echo -e "${GREEN}✅ Sistema pronto para produção!${NC}"
