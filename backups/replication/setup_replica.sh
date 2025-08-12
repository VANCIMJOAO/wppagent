#!/bin/bash
# Configuração do servidor Replica

PRIMARY_HOST=$1
if [ -z "$PRIMARY_HOST" ]; then
    echo "Uso: $0 <primary_host_ip>"
    exit 1
fi

echo "🔧 Configurando servidor Replica..."

# Parar PostgreSQL
sudo systemctl stop postgresql

# Fazer backup do diretório de dados
sudo mv /var/lib/postgresql/*/main /var/lib/postgresql/*/main.backup

# Fazer basebackup do Primary
sudo -u postgres pg_basebackup -h $PRIMARY_HOST -D /var/lib/postgresql/*/main -U replicator -P -W -R

# Configurar recovery
sudo -u postgres cat > /var/lib/postgresql/*/main/postgresql.auto.conf << EOF
primary_conninfo = 'host=$PRIMARY_HOST port=5432 user=replicator'
promote_trigger_file = '/tmp/promote_replica'
EOF

# Iniciar PostgreSQL
sudo systemctl start postgresql

echo "✅ Replica configurado e iniciado"
echo "💡 Para promover a replica a primary: touch /tmp/promote_replica"
