#!/bin/bash
# Script de atualização de senha do banco
echo "Atualizando senha do usuário vancimj no PostgreSQL..."
sudo -u postgres psql -c "ALTER USER vancimj PASSWORD 'q%1#yFDOVuTiVtp^y^XwQdZziFnln#Y*';"
echo "Senha atualizada com sucesso!"
