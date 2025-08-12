#!/bin/bash
# Configuração do servidor Primary para replicação

echo "🔧 Configurando servidor Primary..."

# Backup da configuração atual
sudo cp /etc/postgresql/*/main/postgresql.conf /etc/postgresql/*/main/postgresql.conf.backup
sudo cp /etc/postgresql/*/main/pg_hba.conf /etc/postgresql/*/main/pg_hba.conf.backup

# Criar usuário de replicação
sudo -u postgres psql << EOF
CREATE USER replicator REPLICATION LOGIN ENCRYPTED PASSWORD 'replica_password_here';
EOF

echo "✅ Usuário de replicação criado"

# Aplicar configurações (requer restart do PostgreSQL)
echo "⚠️  Para ativar a replicação, aplique as configurações do postgresql.conf"
echo "⚠️  e reinicie o PostgreSQL: sudo systemctl restart postgresql"
