#!/bin/bash
# Script para configurar SSL com Let's Encrypt (Certbot)
# Para uso em produção com domínio real

DOMAIN=${1:-"whatsapp-agent.com"}
EMAIL=${2:-"admin@whatsapp-agent.com"}

echo "🔐 CONFIGURANDO SSL COM LET'S ENCRYPT"
echo "====================================="
echo "🌐 Domínio: $DOMAIN"
echo "📧 Email: $EMAIL"
echo ""

# Verificar se o domínio foi fornecido
if [ "$DOMAIN" = "whatsapp-agent.com" ]; then
    echo "⚠️  ATENÇÃO: Usando domínio de exemplo!"
    echo "   Use: ./scripts/setup_letsencrypt.sh SEU_DOMINIO.com seu@email.com"
    echo ""
    read -p "Deseja continuar mesmo assim? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Instalar Certbot se não estiver instalado
if ! command -v certbot &> /dev/null; then
    echo "📦 Instalando Certbot..."
    
    # Ubuntu/Debian
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y certbot python3-certbot-nginx
    # CentOS/RHEL
    elif command -v yum &> /dev/null; then
        sudo yum install -y certbot python3-certbot-nginx
    # Fedora
    elif command -v dnf &> /dev/null; then
        sudo dnf install -y certbot python3-certbot-nginx
    else
        echo "❌ Sistema operacional não suportado para instalação automática"
        echo "   Instale o Certbot manualmente: https://certbot.eff.org/"
        exit 1
    fi
    
    echo "✅ Certbot instalado"
fi

# Parar nginx se estiver rodando
if systemctl is-active --quiet nginx; then
    echo "⏹️  Parando nginx temporariamente..."
    sudo systemctl stop nginx
fi

# Gerar certificado
echo "🔑 Gerando certificado SSL..."
sudo certbot certonly \
    --standalone \
    --email "$EMAIL" \
    --agree-tos \
    --no-eff-email \
    -d "$DOMAIN"

if [ $? -eq 0 ]; then
    echo "✅ Certificado gerado com sucesso!"
    
    # Copiar certificados para o diretório do nginx
    SSL_DIR="/home/vancim/whats_agent/config/nginx/ssl"
    
    echo "📋 Copiando certificados..."
    sudo cp "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" "$SSL_DIR/server.crt"
    sudo cp "/etc/letsencrypt/live/$DOMAIN/privkey.pem" "$SSL_DIR/server.key"
    
    # Ajustar permissões
    sudo chown $USER:$USER "$SSL_DIR/server.crt" "$SSL_DIR/server.key"
    chmod 644 "$SSL_DIR/server.crt"
    chmod 600 "$SSL_DIR/server.key"
    
    echo "✅ Certificados copiados para $SSL_DIR"
    
    # Configurar renovação automática
    echo "🔄 Configurando renovação automática..."
    (crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet --post-hook 'systemctl reload nginx'") | crontab -
    
    echo "✅ Renovação automática configurada"
    
    # Atualizar configuração do nginx
    NGINX_CONFIG="/home/vancim/whats_agent/config/nginx/nginx.conf"
    
    # Fazer backup da configuração atual
    cp "$NGINX_CONFIG" "$NGINX_CONFIG.bak.$(date +%Y%m%d_%H%M%S)"
    
    # Substituir server_name na configuração
    sed -i "s/server_name localhost whatsapp-agent.local;/server_name $DOMAIN;/g" "$NGINX_CONFIG"
    sed -i "s/server_name grafana.whatsapp-agent.local;/server_name grafana.$DOMAIN;/g" "$NGINX_CONFIG"
    
    echo "✅ Configuração do nginx atualizada"
    
    # Reiniciar nginx se Docker não estiver sendo usado
    if ! docker-compose ps | grep -q nginx; then
        if systemctl is-available nginx &> /dev/null; then
            sudo systemctl start nginx
            sudo systemctl reload nginx
            echo "✅ Nginx reiniciado"
        fi
    else
        echo "🐳 Reinicie o container nginx: docker-compose restart nginx"
    fi
    
    echo ""
    echo "🎉 SSL CONFIGURADO COM SUCESSO!"
    echo "=============================="
    echo ""
    echo "🌐 Seu site agora está disponível em: https://$DOMAIN"
    echo "📊 Dashboard: https://$DOMAIN/dashboard/"
    echo "📈 Grafana: https://grafana.$DOMAIN"
    echo ""
    echo "📅 Renovação automática configurada para rodar diariamente às 12:00"
    echo "🔍 Verificar status: sudo certbot certificates"
    echo ""
    
else
    echo "❌ Erro ao gerar certificado"
    echo "   Verifique se:"
    echo "   - O domínio $DOMAIN aponta para este servidor"
    echo "   - As portas 80 e 443 estão abertas"
    echo "   - Não há outros serviços usando essas portas"
    exit 1
fi
