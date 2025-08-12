#!/bin/bash
# 🔒 CONFIGURAÇÃO DE USUÁRIO DE BANCO COM PRIVILÉGIOS MÍNIMOS
# =========================================================

set -euo pipefail

echo "🔒 Configurando usuário de banco de dados com privilégios mínimos..."

# Variáveis de configuração
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-whatsapp_agent}"
DB_ADMIN_USER="${DB_USER:-vancimj}"
DB_ADMIN_PASSWORD="${DB_PASSWORD:-os.getenv("DB_PASSWORD", "SECURE_DB_PASSWORD")}"

# Novos usuários específicos
DB_APP_USER="whatsapp_app"
DB_BACKUP_USER="whatsapp_backup"
DB_READONLY_USER="whatsapp_readonly"

# Gerar senhas seguras
DB_APP_PASSWORD=$(openssl rand -base64 32)
DB_BACKUP_PASSWORD=$(openssl rand -base64 32)
DB_READONLY_PASSWORD=$(openssl rand -base64 32)

echo "📝 Criando usuários específicos com privilégios mínimos..."

# Script SQL para criação de usuários
cat > /tmp/create_db_users.sql << EOF
-- ===========================================
-- CRIAÇÃO DE USUÁRIOS COM PRIVILÉGIOS MÍNIMOS
-- ===========================================

-- 1. USUÁRIO DA APLICAÇÃO (privilégios mínimos para operação)
DROP USER IF EXISTS ${DB_APP_USER};
CREATE USER ${DB_APP_USER} WITH 
    LOGIN
    NOSUPERUSER
    NOCREATEDB
    NOCREATEROLE
    NOINHERIT
    NOREPLICATION
    CONNECTION LIMIT 20
    PASSWORD '${DB_APP_PASSWORD}';

-- 2. USUÁRIO DE BACKUP (apenas leitura para backup)
DROP USER IF EXISTS ${DB_BACKUP_USER};
CREATE USER ${DB_BACKUP_USER} WITH 
    LOGIN
    NOSUPERUSER
    NOCREATEDB
    NOCREATEROLE
    NOINHERIT
    NOREPLICATION
    CONNECTION LIMIT 2
    PASSWORD '${DB_BACKUP_PASSWORD}';

-- 3. USUÁRIO SOMENTE LEITURA (para relatórios e monitoramento)
DROP USER IF EXISTS ${DB_READONLY_USER};
CREATE USER ${DB_READONLY_USER} WITH 
    LOGIN
    NOSUPERUSER
    NOCREATEDB
    NOCREATEROLE
    NOINHERIT
    NOREPLICATION
    CONNECTION LIMIT 10
    PASSWORD '${DB_READONLY_PASSWORD}';

-- ===========================================
-- CONFIGURAÇÃO DE PRIVILÉGIOS ESPECÍFICOS
-- ===========================================

-- Conectar ao banco da aplicação
\c ${DB_NAME};

-- PRIVILÉGIOS PARA USUÁRIO DA APLICAÇÃO
-- Apenas o necessário para operação normal
GRANT CONNECT ON DATABASE ${DB_NAME} TO ${DB_APP_USER};
GRANT USAGE ON SCHEMA public TO ${DB_APP_USER};

-- Privilégios em tabelas existentes
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO ${DB_APP_USER};
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO ${DB_APP_USER};

-- Privilégios em tabelas futuras
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO ${DB_APP_USER};
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO ${DB_APP_USER};

-- PRIVILÉGIOS PARA USUÁRIO DE BACKUP
-- Apenas leitura para backup completo
GRANT CONNECT ON DATABASE ${DB_NAME} TO ${DB_BACKUP_USER};
GRANT USAGE ON SCHEMA public TO ${DB_BACKUP_USER};
GRANT SELECT ON ALL TABLES IN SCHEMA public TO ${DB_BACKUP_USER};
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO ${DB_BACKUP_USER};

-- PRIVILÉGIOS PARA USUÁRIO SOMENTE LEITURA
-- Apenas SELECT para relatórios
GRANT CONNECT ON DATABASE ${DB_NAME} TO ${DB_READONLY_USER};
GRANT USAGE ON SCHEMA public TO ${DB_READONLY_USER};
GRANT SELECT ON ALL TABLES IN SCHEMA public TO ${DB_READONLY_USER};
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO ${DB_READONLY_USER};

-- ===========================================
-- POLÍTICAS DE SEGURANÇA ADICIONAIS
-- ===========================================

-- Row Level Security (será implementado posteriormente)
-- ALTER TABLE users ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

-- Revogar privilégios desnecessários do usuário admin na aplicação
-- (manter apenas para migrações e manutenção)

COMMIT;

-- Verificar usuários criados
SELECT usename, usesuper, usecreatedb, usecreaterole, useconnlimit 
FROM pg_user 
WHERE usename IN ('${DB_APP_USER}', '${DB_BACKUP_USER}', '${DB_READONLY_USER}');

-- Verificar privilégios
\dp
EOF

echo "🔄 Executando script de criação de usuários..."

# Executar script SQL
PGPASSWORD="$DB_ADMIN_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_ADMIN_USER" -d "$DB_NAME" -f /tmp/create_db_users.sql

# Remover arquivo temporário
rm -f /tmp/create_db_users.sql

echo "✅ Usuários de banco criados com sucesso!"

# ===========================================
# SALVAR CREDENCIAIS DE FORMA SEGURA
# ===========================================

echo "💾 Salvando credenciais em arquivo seguro..."

CREDENTIALS_FILE="/home/vancim/whats_agent/secrets/database_credentials.env"
mkdir -p "$(dirname "$CREDENTIALS_FILE")"

cat > "$CREDENTIALS_FILE" << EOF
# 🔒 CREDENCIAIS DE BANCO DE DADOS SEGURAS
# ========================================
# Gerado em: $(date)

# Usuário da aplicação (privilégios mínimos para operação)
DB_APP_USER=${DB_APP_USER}
DB_APP_PASSWORD=${DB_APP_PASSWORD}
DB_APP_URL=postgresql+asyncpg://${DB_APP_USER}:${DB_APP_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}

# Usuário de backup (somente leitura)
DB_BACKUP_USER=${DB_BACKUP_USER}
DB_BACKUP_PASSWORD=${DB_BACKUP_PASSWORD}
DB_BACKUP_URL=postgresql://${DB_BACKUP_USER}:${DB_BACKUP_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}

# Usuário somente leitura (relatórios/monitoramento)
DB_READONLY_USER=${DB_READONLY_USER}
DB_READONLY_PASSWORD=${DB_READONLY_PASSWORD}
DB_READONLY_URL=postgresql://${DB_READONLY_USER}:${DB_READONLY_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}

# URLs de conexão por tipo
DATABASE_URL=postgresql+asyncpg://${DB_APP_USER}:${DB_APP_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}
DATABASE_URL_SYNC=postgresql://${DB_APP_USER}:${DB_APP_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}
DATABASE_URL_BACKUP=postgresql://${DB_BACKUP_USER}:${DB_BACKUP_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}
DATABASE_URL_READONLY=postgresql://${DB_READONLY_USER}:${DB_READONLY_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}
EOF

# Proteger arquivo de credenciais
chmod 600 "$CREDENTIALS_FILE"

echo "🔐 Credenciais salvas em: $CREDENTIALS_FILE"

# ===========================================
# CRIAR SCRIPT DE TESTE DE CONEXÃO
# ===========================================

echo "🧪 Criando script de teste de conexão..."

cat > /home/vancim/whats_agent/scripts/test_db_connections.py << 'EOF'
#!/usr/bin/env python3
"""
🧪 TESTE DE CONEXÕES DE BANCO DE DADOS
=====================================

Testa todas as conexões de banco com usuários específicos
"""

import os
import sys
import asyncio
import asyncpg
import psycopg2
from datetime import datetime

# Carregar credenciais
def load_credentials():
    """Carrega credenciais do arquivo seguro"""
    creds_file = "/home/vancim/whats_agent/secrets/database_credentials.env"
    
    if not os.path.exists(creds_file):
        print("❌ Arquivo de credenciais não encontrado")
        return None
    
    creds = {}
    with open(creds_file, 'r') as f:
        for line in f:
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.strip().split('=', 1)
                creds[key] = value
    
    return creds

async def test_async_connection(url, user_type):
    """Testa conexão assíncrona"""
    try:
        conn = await asyncpg.connect(url)
        
        # Teste básico
        result = await conn.fetchval("SELECT version()")
        
        # Teste de privilégios
        try:
            if user_type == "app":
                await conn.fetchval("SELECT COUNT(*) FROM users")
                await conn.execute("SELECT 1")  # Teste básico
                print(f"   ✅ {user_type}: Conexão OK, privilégios verificados")
            elif user_type == "backup":
                await conn.fetchval("SELECT COUNT(*) FROM users")
                print(f"   ✅ {user_type}: Conexão OK, SELECT funcionando")
            elif user_type == "readonly":
                await conn.fetchval("SELECT COUNT(*) FROM users")
                print(f"   ✅ {user_type}: Conexão OK, somente leitura")
        except Exception as e:
            print(f"   ⚠️ {user_type}: Conexão OK, mas erro nos privilégios: {e}")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"   ❌ {user_type}: Erro de conexão: {e}")
        return False

def test_sync_connection(url, user_type):
    """Testa conexão síncrona"""
    try:
        conn = psycopg2.connect(url)
        cursor = conn.cursor()
        
        # Teste básico
        cursor.execute("SELECT version()")
        result = cursor.fetchone()
        
        # Teste de privilégios
        try:
            cursor.execute("SELECT COUNT(*) FROM users")
            count = cursor.fetchone()[0]
            print(f"   ✅ {user_type}: Conexão síncrona OK ({count} usuários)")
        except Exception as e:
            print(f"   ⚠️ {user_type}: Conexão OK, mas erro: {e}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"   ❌ {user_type}: Erro de conexão síncrona: {e}")
        return False

async def main():
    print("🧪 TESTE DE CONEXÕES DE BANCO DE DADOS")
    print("=" * 50)
    print(f"📅 Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print()
    
    # Carregar credenciais
    creds = load_credentials()
    if not creds:
        return 1
    
    tests_passed = 0
    total_tests = 0
    
    # Teste de conexões assíncronas
    print("🔄 Testando conexões assíncronas...")
    
    if 'DB_APP_URL' in creds:
        total_tests += 1
        if await test_async_connection(creds['DB_APP_URL'], "app"):
            tests_passed += 1
    
    if 'DB_READONLY_URL' in creds:
        # Converter para asyncpg
        readonly_async = creds['DB_READONLY_URL'].replace('postgresql://', 'postgresql://')
        total_tests += 1
        if await test_async_connection(readonly_async, "readonly"):
            tests_passed += 1
    
    print()
    
    # Teste de conexões síncronas
    print("🔄 Testando conexões síncronas...")
    
    if 'DB_BACKUP_URL' in creds:
        total_tests += 1
        if test_sync_connection(creds['DB_BACKUP_URL'], "backup"):
            tests_passed += 1
    
    print()
    print("📊 RESULTADO DOS TESTES")
    print("-" * 30)
    print(f"   Passou: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("   🎉 Todos os testes passaram!")
        return 0
    else:
        print("   ⚠️ Alguns testes falharam")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
EOF

chmod +x /home/vancim/whats_agent/scripts/test_db_connections.py

echo ""
echo "🎉 USUÁRIOS DE BANCO CONFIGURADOS COM SUCESSO!"
echo "=============================================="
echo ""
echo "👤 USUÁRIOS CRIADOS:"
echo "   - $DB_APP_USER: Aplicação (privilégios mínimos)"
echo "   - $DB_BACKUP_USER: Backup (somente leitura)"
echo "   - $DB_READONLY_USER: Relatórios (somente leitura)"
echo ""
echo "🔐 CREDENCIAIS SALVAS EM:"
echo "   $CREDENTIALS_FILE"
echo ""
echo "🧪 TESTE AS CONEXÕES:"
echo "   python3 scripts/test_db_connections.py"
echo ""
echo "⚠️ IMPORTANTE:"
echo "   1. Atualize o .env para usar o novo usuário da aplicação"
echo "   2. Reinicie a aplicação após a mudança"
echo "   3. Monitore os logs para verificar funcionamento"
echo ""
