#!/bin/bash

# Iniciar HashiCorp Vault em modo desenvolvimento

echo "🔐 Iniciando Vault em modo desenvolvimento..."

# Verificar se Vault está instalado
if ! command -v vault &> /dev/null; then
    echo "⚠️ Vault não encontrado. Instalando..."
    
    # Download Vault
    curl -fsSL https://apt.releases.hashicorp.com/gpg | sudo apt-key add -
    sudo apt-add-repository "deb [arch=amd64] https://apt.releases.hashicorp.com $(lsb_release -cs) main"
    sudo apt-get update && sudo apt-get install vault
fi

# Iniciar Vault dev server
vault server -dev -dev-root-token-id="root" -dev-listen-address="0.0.0.0:8200" &

VAULT_PID=$!
echo "🔐 Vault iniciado (PID: $VAULT_PID)"
echo "🌐 Vault UI: http://localhost:8200"
echo "🔑 Root Token: root"

# Configurar ambiente
export VAULT_ADDR='http://127.0.0.1:8200'
export VAULT_TOKEN='root'

# Aguardar Vault inicializar
sleep 5

# Habilitar engines de secrets
vault auth enable userpass
vault secrets enable -path=database kv-v2
vault secrets enable -path=apis kv-v2
vault secrets enable -path=whatsapp kv-v2
vault secrets enable -path=general kv-v2

echo "✅ Vault configurado"
echo "💡 Execute 'export VAULT_ADDR=http://127.0.0.1:8200 && export VAULT_TOKEN=root' para usar o Vault"

# Aguardar sinal para parar
wait $VAULT_PID
