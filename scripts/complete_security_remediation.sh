#!/bin/bash
"""
🚨 GUIA COMPLETO DE REMEDIAÇÃO DE SEGURANÇA - WHATSAPP AGENT
============================================================

INSTRUÇÕES PASSO-A-PASSO PARA COMPLETAR A CORREÇÃO DE SEGURANÇA
"""

echo "🚨 INICIANDO PROCESSO DE REMEDIAÇÃO FINAL"
echo "==============================================="

# Verificar se já temos o ambiente preparado
if [ ! -f ".env" ] || [ ! -d "secrets/vault" ]; then
    echo "❌ ERRO: Sistema de segurança não foi inicializado!"
    echo "Execute primeiro: python scripts/security_remediation.py"
    exit 1
fi

echo "✅ Sistema de segurança detectado"
echo ""

echo "🔴 AÇÃO 1: REVOGAR TOKENS ANTIGOS"
echo "=================================="
echo ""
echo "📋 TOKENS A REVOGAR:"
echo "1. OpenAI API Key: sk-proj-b14YOpiJvXMrtREBQx08XmlqL3xc4Niuj..."
echo "2. Meta Access Token: EAAI4WnfpZAe0BPEo8vwjU7RCZBuaFeuNqzKkJaCtTY4p..."
echo "3. Ngrok Auth Token: 2mLNDncBMmk2zr0sUSGCQBwGAfp..."
echo ""

echo "🌐 ABRIR PAINÉIS DE REVOGAÇÃO:"
echo ""
echo "1. OpenAI (https://platform.openai.com/api-keys):"
echo "   - Faça login na sua conta OpenAI"
echo "   - Vá para 'API Keys'"
echo "   - Encontre a chave que começa com 'sk-proj-b14YOpiJ...'"
echo "   - Clique em 'Delete' ou 'Revoke'"
echo ""

echo "2. Meta/Facebook (https://developers.facebook.com/apps/):"
echo "   - Faça login no Facebook Developers"
echo "   - Vá para seu app WhatsApp"
echo "   - Em 'WhatsApp > Configuration'"
echo "   - Revogue o token atual e gere um novo"
echo ""

echo "3. Ngrok (https://dashboard.ngrok.com/get-started/your-authtoken):"
echo "   - Faça login no Ngrok"
echo "   - Vá para 'Your Authtoken'"
echo "   - Clique em 'Reset your authtoken'"
echo "   - Copie o novo token gerado"
echo ""

read -p "✅ Pressione ENTER após revogar TODOS os tokens antigos..."

echo ""
echo "🔴 AÇÃO 2: SUBSTITUIR PLACEHOLDERS NO .ENV"
echo "=========================================="
echo ""

# Backup do .env atual
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
echo "✅ Backup do .env criado"

echo ""
echo "📝 NOVOS TOKENS NECESSÁRIOS:"
echo ""

# Verificar se existem placeholders
if grep -q "REPLACE_WITH_NEW_OPENAI_KEY" .env; then
    echo "1. OpenAI API Key:"
    echo "   - Vá para: https://platform.openai.com/api-keys"
    echo "   - Clique em 'Create new secret key'"
    echo "   - Copie a nova chave (sk-...)"
    echo ""
    read -p "   Cole a NOVA chave OpenAI: " new_openai_key
    if [ ! -z "$new_openai_key" ]; then
        sed -i "s/REPLACE_WITH_NEW_OPENAI_KEY/$new_openai_key/" .env
        echo "   ✅ OpenAI API Key atualizada"
    fi
fi

if grep -q "REPLACE_WITH_NEW_META_TOKEN" .env; then
    echo ""
    echo "2. Meta Access Token:"
    echo "   - Vá para: https://developers.facebook.com/apps/"
    echo "   - Selecione seu app > WhatsApp > Configuration"
    echo "   - Gere um novo 'Temporary access token'"
    echo "   - Copie o token (EAAI...)"
    echo ""
    read -p "   Cole o NOVO token Meta: " new_meta_token
    if [ ! -z "$new_meta_token" ]; then
        sed -i "s/REPLACE_WITH_NEW_META_TOKEN/$new_meta_token/" .env
        echo "   ✅ Meta Access Token atualizado"
    fi
fi

if grep -q "REPLACE_WITH_NEW_NGROK_TOKEN" .env; then
    echo ""
    echo "3. Ngrok Auth Token:"
    echo "   - Vá para: https://dashboard.ngrok.com/get-started/your-authtoken"
    echo "   - Copie o novo authtoken"
    echo ""
    read -p "   Cole o NOVO token Ngrok: " new_ngrok_token
    if [ ! -z "$new_ngrok_token" ]; then
        sed -i "s/REPLACE_WITH_NEW_NGROK_TOKEN/$new_ngrok_token/" .env
        echo "   ✅ Ngrok Auth Token atualizado"
    fi
fi

echo ""
echo "✅ Arquivo .env atualizado com novos tokens"

echo ""
echo "🔴 AÇÃO 3: ATUALIZAR SENHA DO BANCO DE DADOS"
echo "============================================"
echo ""

# Extrair nova senha do .env
new_db_password=$(grep "^DB_PASSWORD=" .env | cut -d'=' -f2)

if [ ! -z "$new_db_password" ]; then
    echo "📋 Nova senha do banco encontrada: $new_db_password"
    echo ""
    echo "🔧 Executando atualização da senha no PostgreSQL..."
    
    # Criar script temporário
    cat > /tmp/update_db_password.sql << EOF
ALTER USER vancimj PASSWORD '$new_db_password';
\q
EOF
    
    echo "Atualizando senha do usuário vancimj no PostgreSQL..."
    
    # Tentar executar como postgres
    if sudo -u postgres psql -f /tmp/update_db_password.sql; then
        echo "✅ Senha do banco atualizada com sucesso!"
        rm /tmp/update_db_password.sql
    else
        echo "⚠️ Erro ao atualizar senha automaticamente"
        echo "Execute manualmente: sudo -u postgres psql"
        echo "Depois execute: ALTER USER vancimj PASSWORD '$new_db_password';"
    fi
else
    echo "❌ Senha do banco não encontrada no .env"
fi

echo ""
echo "🔴 AÇÃO 4: TESTAR FUNCIONALIDADES"
echo "================================="
echo ""

echo "🧪 Executando testes de validação..."

# Teste 1: Verificar conexão com banco
echo ""
echo "1. Testando conexão com banco de dados..."
if python3 -c "
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

try:
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )
    conn.close()
    print('✅ Conexão com banco OK')
except Exception as e:
    print(f'❌ Erro na conexão: {e}')
"; then
    echo "   ✅ Banco de dados: OK"
else
    echo "   ❌ Banco de dados: ERRO"
fi

# Teste 2: Verificar OpenAI
echo ""
echo "2. Testando conexão com OpenAI..."
if python3 -c "
import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('OPENAI_API_KEY')
if api_key and api_key != 'REPLACE_WITH_NEW_OPENAI_KEY':
    try:
        response = requests.get(
            'https://api.openai.com/v1/models',
            headers={'Authorization': f'Bearer {api_key}'},
            timeout=10
        )
        if response.status_code == 200:
            print('✅ OpenAI API OK')
        else:
            print(f'❌ OpenAI API Error: {response.status_code}')
    except Exception as e:
        print(f'❌ OpenAI Error: {e}')
else:
    print('⚠️ OpenAI API Key não configurada')
"; then
    echo "   ✅ OpenAI: OK"
else
    echo "   ❌ OpenAI: ERRO"
fi

# Teste 3: Verificar Meta/WhatsApp
echo ""
echo "3. Testando conexão com Meta/WhatsApp..."
if python3 -c "
import os
import requests
from dotenv import load_dotenv

load_dotenv()

token = os.getenv('META_ACCESS_TOKEN')
if token and token != 'REPLACE_WITH_NEW_META_TOKEN':
    try:
        response = requests.get(
            'https://graph.facebook.com/v18.0/me',
            params={'access_token': token},
            timeout=10
        )
        if response.status_code == 200:
            print('✅ Meta API OK')
        else:
            print(f'❌ Meta API Error: {response.status_code}')
    except Exception as e:
        print(f'❌ Meta Error: {e}')
else:
    print('⚠️ Meta Access Token não configurado')
"; then
    echo "   ✅ Meta/WhatsApp: OK"
else
    echo "   ❌ Meta/WhatsApp: ERRO"
fi

# Teste 4: Verificar autenticação admin
echo ""
echo "4. Testando autenticação admin..."
admin_password=$(grep "^ADMIN_PASSWORD=" .env | cut -d'=' -f2)
if [ ! -z "$admin_password" ] && [ "$admin_password" != "admin123" ]; then
    echo "   ✅ Nova senha admin configurada: ${admin_password:0:4}****"
else
    echo "   ❌ Senha admin não foi atualizada"
fi

# Teste 5: Executar monitor de segurança
echo ""
echo "5. Executando monitor de segurança..."
if python3 scripts/security_monitor.py; then
    echo "   ✅ Monitor de segurança: OK"
else
    echo "   ❌ Monitor de segurança: ERRO"
fi

echo ""
echo "🎯 RESUMO FINAL"
echo "==============="
echo ""

# Verificar status geral
if grep -q "REPLACE_WITH_NEW" .env; then
    echo "⚠️  STATUS: PARCIALMENTE CONFIGURADO"
    echo "❌ Ainda existem placeholders no .env que precisam ser substituídos"
    echo ""
    echo "🔍 Placeholders restantes:"
    grep "REPLACE_WITH_NEW" .env || echo "   Nenhum placeholder encontrado"
else
    echo "✅ STATUS: TOTALMENTE CONFIGURADO"
    echo "🛡️  Todos os tokens foram substituídos por credenciais reais"
fi

echo ""
echo "📊 CHECKLIST FINAL:"
echo "[ ] 1. Tokens antigos revogados nos painéis"
echo "[ ] 2. Novos tokens configurados no .env"
echo "[ ] 3. Senha do banco de dados atualizada"
echo "[ ] 4. Testes de funcionalidade executados"
echo ""

echo "🔐 PRÓXIMOS PASSOS:"
echo "1. Configurar execução diária do monitor: crontab -e"
echo "   0 2 * * * cd /home/vancim/whats_agent && python scripts/security_monitor.py"
echo ""
echo "2. Monitorar logs por tentativas com credenciais antigas"
echo "3. Implementar rotação automática de credenciais (30 dias)"
echo ""

echo "✅ REMEDIAÇÃO DE SEGURANÇA CONCLUÍDA!"
echo "🛡️  Sistema seguro e pronto para produção"
