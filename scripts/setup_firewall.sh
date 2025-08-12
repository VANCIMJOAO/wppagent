#!/bin/bash
# 🔥 CONFIGURAÇÃO DE FIREWALL ULTRA-SEGURA
# ========================================

set -euo pipefail

echo "🔥 Configurando Firewall com UFW..."

# Instalar UFW se não estiver instalado
if ! command -v ufw &> /dev/null; then
    echo "📦 Instalando UFW..."
    sudo apt-get update
    sudo apt-get install -y ufw
fi

# Reset UFW para estado padrão
echo "🔄 Resetando UFW..."
sudo ufw --force reset

# Política padrão: NEGAR TUDO
echo "🚫 Configurando política padrão (DENY ALL)..."
sudo ufw default deny incoming
sudo ufw default deny outgoing
sudo ufw default deny forward

# ===========================================
# REGRAS DE ENTRADA (INCOMING)
# ===========================================

echo "📥 Configurando regras de entrada..."

# SSH - Apenas da rede local (ajustar conforme necessário)
sudo ufw allow from 192.168.0.0/16 to any port 22 proto tcp comment "SSH - Rede Local"
sudo ufw allow from 10.0.0.0/8 to any port 22 proto tcp comment "SSH - Rede Privada"
sudo ufw allow from 172.16.0.0/12 to any port 22 proto tcp comment "SSH - Docker Networks"

# HTTP/HTTPS - Público (apenas essas portas)
sudo ufw allow 80/tcp comment "HTTP"
sudo ufw allow 443/tcp comment "HTTPS"

# DNS - Necessário para resolução de nomes
sudo ufw allow out 53 comment "DNS"

# NTP - Sincronização de tempo
sudo ufw allow out 123 comment "NTP"

# ===========================================
# REGRAS DE SAÍDA (OUTGOING) - RESTRITIVAS
# ===========================================

echo "📤 Configurando regras de saída..."

# HTTPS para atualizações e APIs externas
sudo ufw allow out 443/tcp comment "HTTPS Outbound"

# HTTP para alguns repositórios
sudo ufw allow out 80/tcp comment "HTTP Outbound"

# WhatsApp Business API
sudo ufw allow out 443/tcp to graph.facebook.com comment "Meta WhatsApp API"

# OpenAI API
sudo ufw allow out 443/tcp to api.openai.com comment "OpenAI API"

# PostgreSQL (apenas interno)
sudo ufw allow from 172.22.0.0/24 to 172.22.0.0/24 port 5432 proto tcp comment "PostgreSQL Internal"

# Redis (apenas interno)
sudo ufw allow from 172.21.0.0/24 to 172.21.0.0/24 port 6379 proto tcp comment "Redis Internal"

# ===========================================
# PROTEÇÃO CONTRA ATAQUES
# ===========================================

echo "🛡️ Configurando proteção contra ataques..."

# Rate limiting para SSH
sudo ufw limit ssh comment "SSH Rate Limiting"

# Bloquear ranges de IPs maliciosos conhecidos
# (Adicionar conforme necessário)

# Bloquear países específicos (opcional)
# sudo ufw deny from 1.2.3.0/24 comment "Block Malicious Range"

# ===========================================
# LOGGING AVANÇADO
# ===========================================

echo "📝 Configurando logging..."
sudo ufw logging on

# ===========================================
# DOCKER COMPATIBILITY
# ===========================================

echo "🐳 Configurando compatibilidade com Docker..."

# Permitir tráfego interno do Docker
sudo ufw allow from 172.17.0.0/16 comment "Docker Default Bridge"
sudo ufw allow from 172.20.0.0/24 comment "Frontend Network"
sudo ufw allow from 172.21.0.0/24 comment "Backend Network"
sudo ufw allow from 172.22.0.0/24 comment "Database Network"

# ===========================================
# REGRAS ESPECÍFICAS PARA MONITORAMENTO
# ===========================================

echo "📊 Configurando regras para monitoramento..."

# Prometheus (apenas interno)
sudo ufw allow from 172.21.0.0/24 to 172.21.0.0/24 port 9090 proto tcp comment "Prometheus Internal"

# Grafana (apenas interno)
sudo ufw allow from 172.21.0.0/24 to 172.21.0.0/24 port 3000 proto tcp comment "Grafana Internal"

# ===========================================
# PROTEÇÕES ADICIONAIS
# ===========================================

echo "🔒 Configurando proteções adicionais..."

# Bloquear ping (opcional)
# echo 'net.ipv4.icmp_echo_ignore_all = 1' | sudo tee -a /etc/sysctl.conf

# Proteção contra SYN flood
echo 'net.ipv4.tcp_syncookies = 1' | sudo tee -a /etc/sysctl.conf
echo 'net.ipv4.tcp_max_syn_backlog = 2048' | sudo tee -a /etc/sysctl.conf
echo 'net.ipv4.tcp_synack_retries = 3' | sudo tee -a /etc/sysctl.conf

# Proteção contra IP spoofing
echo 'net.ipv4.conf.all.rp_filter = 1' | sudo tee -a /etc/sysctl.conf
echo 'net.ipv4.conf.default.rp_filter = 1' | sudo tee -a /etc/sysctl.conf

# Desabilitar redirecionamentos ICMP
echo 'net.ipv4.conf.all.accept_redirects = 0' | sudo tee -a /etc/sysctl.conf
echo 'net.ipv6.conf.all.accept_redirects = 0' | sudo tee -a /etc/sysctl.conf

# Desabilitar source routing
echo 'net.ipv4.conf.all.accept_source_route = 0' | sudo tee -a /etc/sysctl.conf
echo 'net.ipv6.conf.all.accept_source_route = 0' | sudo tee -a /etc/sysctl.conf

# ===========================================
# ATIVAR FIREWALL
# ===========================================

echo "🔥 Ativando firewall..."
sudo ufw --force enable

# ===========================================
# CONFIGURAR FAIL2BAN
# ===========================================

echo "🛡️ Configurando Fail2Ban..."

# Instalar Fail2Ban
if ! command -v fail2ban-server &> /dev/null; then
    echo "📦 Instalando Fail2Ban..."
    sudo apt-get install -y fail2ban
fi

# Configuração do Fail2Ban
sudo tee /etc/fail2ban/jail.local > /dev/null << 'EOF'
[DEFAULT]
# Configuração padrão ultra-restritiva
bantime = 3600
findtime = 600
maxretry = 3
backend = systemd

# Whitelist de IPs confiáveis
ignoreip = 127.0.0.1/8 ::1 192.168.0.0/16 10.0.0.0/8

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 7200

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
port = http,https
logpath = /var/log/nginx/error.log
maxretry = 3

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
port = http,https
logpath = /var/log/nginx/error.log
maxretry = 5

[nginx-botsearch]
enabled = true
filter = nginx-botsearch
port = http,https
logpath = /var/log/nginx/access.log
maxretry = 2
EOF

# Restart Fail2Ban
sudo systemctl restart fail2ban
sudo systemctl enable fail2ban

# ===========================================
# RELATÓRIO FINAL
# ===========================================

echo ""
echo "🎉 FIREWALL CONFIGURADO COM SUCESSO!"
echo "===================================="
echo ""
echo "📊 STATUS DO FIREWALL:"
sudo ufw status verbose
echo ""
echo "📊 STATUS DO FAIL2BAN:"
sudo fail2ban-client status
echo ""
echo "⚠️ IMPORTANTE:"
echo "1. Teste a conectividade SSH antes de desconectar"
echo "2. Monitore os logs: sudo tail -f /var/log/ufw.log"
echo "3. Ajuste as regras conforme necessário"
echo "4. Para emergência: sudo ufw disable"
echo ""
echo "🔍 COMANDOS ÚTEIS:"
echo "- Ver status: sudo ufw status"
echo "- Ver logs: sudo tail -f /var/log/ufw.log"
echo "- Ver Fail2Ban: sudo fail2ban-client status"
echo "- Aplicar sysctl: sudo sysctl -p"
echo ""
