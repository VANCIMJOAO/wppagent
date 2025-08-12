#!/bin/bash
# Script para gerar certificados SSL auto-assinados
# Para desenvolvimento e teste local

SSL_DIR="/home/vancim/whats_agent/config/nginx/ssl"
DAYS=365
COUNTRY="BR"
STATE="SP"
CITY="Sao Paulo"
ORGANIZATION="WhatsApp Agent"
UNIT="IT Department"
COMMON_NAME="whatsapp-agent.local"

echo "🔐 GERANDO CERTIFICADOS SSL PARA WHATSAPP AGENT"
echo "=============================================="

# Criar diretório se não existir
mkdir -p "$SSL_DIR"

# Gerar chave privada
echo "🔑 Gerando chave privada..."
openssl genrsa -out "$SSL_DIR/server.key" 2048

# Gerar certificado auto-assinado
echo "📜 Gerando certificado auto-assinado..."
openssl req -new -x509 -key "$SSL_DIR/server.key" -out "$SSL_DIR/server.crt" -days $DAYS -subj "/C=$COUNTRY/ST=$STATE/L=$CITY/O=$ORGANIZATION/OU=$UNIT/CN=$COMMON_NAME"

# Definir permissões
chmod 600 "$SSL_DIR/server.key"
chmod 644 "$SSL_DIR/server.crt"

echo "✅ Certificados gerados com sucesso!"
echo "📁 Localização: $SSL_DIR"
echo "🔑 Chave privada: server.key"
echo "📜 Certificado: server.crt"
echo ""
echo "⚠️  IMPORTANTE:"
echo "   - Estes são certificados auto-assinados para desenvolvimento"
echo "   - Para produção, use certificados de uma CA válida (Let's Encrypt)"
echo "   - Adicione '$COMMON_NAME' ao seu /etc/hosts se necessário"
echo ""
echo "🚀 Para produção com Let's Encrypt, use:"
echo "   certbot --nginx -d seu-dominio.com"
