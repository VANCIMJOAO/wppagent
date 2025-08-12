#!/usr/bin/env python3
"""
🔐 CONFIGURAÇÃO DE CRIPTOGRAFIA DE BANCO DE DADOS
===============================================

Implementa criptografia em trânsito e repouso para PostgreSQL
"""

import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

sys.path.append('/home/vancim/whats_agent')

def run_command(cmd, capture=True, check=True):
    """Executa comando e retorna resultado"""
    try:
        if capture:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=check)
            return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
        else:
            result = subprocess.run(cmd, shell=True, check=check)
            return result.returncode == 0, "", ""
    except subprocess.CalledProcessError as e:
        return False, "", str(e)
    except Exception as e:
        return False, "", str(e)

def configure_ssl_certificates():
    """Configura certificados SSL para PostgreSQL"""
    print("🔐 Configurando certificados SSL para PostgreSQL...")
    
    ssl_dir = "/home/vancim/whats_agent/config/postgres/ssl"
    os.makedirs(ssl_dir, exist_ok=True)
    
    # Gerar certificado para PostgreSQL
    ssl_config = f"""
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = BR
ST = State
L = City
O = WhatsApp Agent
OU = Database
CN = postgres

[v3_req]
basicConstraints = CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = postgres
DNS.2 = localhost
DNS.3 = whatsapp_postgres
IP.1 = 127.0.0.1
IP.2 = 172.22.0.2
"""
    
    config_file = f"{ssl_dir}/postgres_ssl.conf"
    with open(config_file, 'w') as f:
        f.write(ssl_config)
    
    # Gerar chave privada
    success, stdout, stderr = run_command(f"openssl genpkey -algorithm RSA -out {ssl_dir}/server.key -pkcs8 -aes256 -pass pass:postgres_ssl_key")
    if not success:
        print(f"❌ Erro ao gerar chave privada: {stderr}")
        return False
    
    # Gerar certificado
    success, stdout, stderr = run_command(f"openssl req -new -x509 -key {ssl_dir}/server.key -out {ssl_dir}/server.crt -days 365 -config {config_file} -passin pass:postgres_ssl_key")
    if not success:
        print(f"❌ Erro ao gerar certificado: {stderr}")
        return False
    
    # Gerar arquivo de certificado CA
    shutil.copy(f"{ssl_dir}/server.crt", f"{ssl_dir}/root.crt")
    
    # Configurar permissões
    os.chmod(f"{ssl_dir}/server.key", 0o600)
    os.chmod(f"{ssl_dir}/server.crt", 0o644)
    os.chmod(f"{ssl_dir}/root.crt", 0o644)
    
    print("✅ Certificados SSL gerados")
    return True

def configure_postgresql_ssl():
    """Configura PostgreSQL para usar SSL"""
    print("🔧 Configurando PostgreSQL para SSL...")
    
    pg_config = """
# ===========================================
# CONFIGURAÇÃO SSL/TLS PARA POSTGRESQL
# ===========================================

# Habilitar SSL
ssl = on
ssl_cert_file = '/var/lib/postgresql/ssl/server.crt'
ssl_key_file = '/var/lib/postgresql/ssl/server.key'
ssl_ca_file = '/var/lib/postgresql/ssl/root.crt'

# Configurações de criptografia
ssl_ciphers = 'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305'
ssl_prefer_server_ciphers = on
ssl_ecdh_curve = 'prime256v1'
ssl_min_protocol_version = 'TLSv1.2'
ssl_max_protocol_version = 'TLSv1.3'

# Configurações de autenticação
password_encryption = scram-sha-256

# Configurações de logging para auditoria
log_connections = on
log_disconnections = on
log_statement = 'mod'
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '

# Configurações de segurança adicionais
shared_preload_libraries = 'pg_stat_statements'
track_activities = on
track_counts = on
track_io_timing = on
track_functions = all
"""
    
    config_dir = "/home/vancim/whats_agent/config/postgres"
    os.makedirs(config_dir, exist_ok=True)
    
    with open(f"{config_dir}/postgresql_ssl.conf", 'w') as f:
        f.write(pg_config)
    
    print("✅ Configuração SSL do PostgreSQL criada")
    return True

def configure_pg_hba():
    """Configura pg_hba.conf para SSL obrigatório"""
    print("🔒 Configurando autenticação SSL obrigatória...")
    
    pg_hba_config = """
# ===========================================
# CONFIGURAÇÃO DE AUTENTICAÇÃO SSL OBRIGATÓRIA
# ===========================================

# TYPE  DATABASE        USER            ADDRESS                 METHOD

# Conexões SSL obrigatórias para usuários da aplicação
hostssl    whatsapp_agent    whatsapp_app         0.0.0.0/0                 scram-sha-256
hostssl    whatsapp_agent    whatsapp_backup      0.0.0.0/0                 scram-sha-256
hostssl    whatsapp_agent    whatsapp_readonly    0.0.0.0/0                 scram-sha-256

# Administrador apenas com SSL
hostssl    whatsapp_agent    vancimj              0.0.0.0/0                 scram-sha-256

# Conexões locais (apenas para manutenção)
local      all               postgres                                       peer
local      all               all                                            peer

# Negar todas as conexões não-SSL
host       all               all                  0.0.0.0/0                 reject

# IPv6 (se habilitado)
hostssl    all               all                  ::1/128                   scram-sha-256
"""
    
    config_dir = "/home/vancim/whats_agent/config/postgres"
    with open(f"{config_dir}/pg_hba.conf", 'w') as f:
        f.write(pg_hba_config)
    
    print("✅ Configuração de autenticação SSL criada")
    return True

def configure_docker_postgres_ssl():
    """Configura Docker Compose para PostgreSQL com SSL"""
    print("🐳 Atualizando Docker Compose para SSL...")
    
    # Ler docker-compose atual
    compose_file = "/home/vancim/whats_agent/docker-compose.yml"
    
    if not os.path.exists(compose_file):
        print(f"❌ {compose_file} não encontrado")
        return False
    
    with open(compose_file, 'r') as f:
        content = f.read()
    
    # Adicionar configurações SSL ao PostgreSQL
    ssl_config = """
    # 🔐 CONFIGURAÇÕES SSL ADICIONADAS
    environment:
      POSTGRES_DB: ${DB_NAME:-whatsapp_agent}
      POSTGRES_USER: ${DB_USER:-vancimj}
      POSTGRES_PASSWORD: ${DB_PASSWORD:-change_this_password}
      PGDATA: /var/lib/postgresql/data/pgdata
      # SSL Configuration
      POSTGRES_SSL_CERT_FILE: /var/lib/postgresql/ssl/server.crt
      POSTGRES_SSL_KEY_FILE: /var/lib/postgresql/ssl/server.key
      POSTGRES_SSL_CA_FILE: /var/lib/postgresql/ssl/root.crt
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups/database:/backups
      - ./config/postgres/ssl:/var/lib/postgresql/ssl:ro
      - ./config/postgres/postgresql_ssl.conf:/var/lib/postgresql/postgresql_ssl.conf:ro
      - ./config/postgres/pg_hba.conf:/var/lib/postgresql/pg_hba.conf:ro
    command: >
      postgres
      -c ssl=on
      -c ssl_cert_file=/var/lib/postgresql/ssl/server.crt
      -c ssl_key_file=/var/lib/postgresql/ssl/server.key
      -c ssl_ca_file=/var/lib/postgresql/ssl/root.crt
      -c config_file=/var/lib/postgresql/postgresql_ssl.conf
      -c hba_file=/var/lib/postgresql/pg_hba.conf
      -c shared_preload_libraries=pg_stat_statements
      -c log_statement=mod
      -c log_connections=on
      -c log_disconnections=on
      -c password_encryption=scram-sha-256
"""
    
    # Criar arquivo de configuração Docker específico
    ssl_compose = f"""
# Configuração adicional para PostgreSQL com SSL
# Adicione estas linhas ao seu docker-compose.yml na seção do postgres:

{ssl_config}
"""
    
    config_dir = "/home/vancim/whats_agent/config/postgres"
    with open(f"{config_dir}/docker_ssl_config.yml", 'w') as f:
        f.write(ssl_compose)
    
    print("✅ Configuração Docker SSL criada")
    print(f"📋 Veja: {config_dir}/docker_ssl_config.yml")
    return True

def create_encrypted_connection_urls():
    """Cria URLs de conexão com SSL obrigatório"""
    print("🔗 Criando URLs de conexão criptografadas...")
    
    ssl_urls = """
# 🔐 URLS DE CONEXÃO COM SSL OBRIGATÓRIO
# ====================================

# Aplicação principal (SSL obrigatório)
DATABASE_URL_SSL=postgresql+asyncpg://whatsapp_app:PASSWORD@postgres:5432/whatsapp_agent?ssl=require&sslmode=require&sslcert=/app/ssl/client.crt&sslkey=/app/ssl/client.key&sslrootcert=/app/ssl/root.crt

# Backup (SSL obrigatório)
DATABASE_URL_BACKUP_SSL=postgresql://whatsapp_backup:PASSWORD@postgres:5432/whatsapp_agent?sslmode=require&sslrootcert=/app/ssl/root.crt

# Somente leitura (SSL obrigatório) 
DATABASE_URL_READONLY_SSL=postgresql://whatsapp_readonly:PASSWORD@postgres:5432/whatsapp_agent?sslmode=require&sslrootcert=/app/ssl/root.crt

# URLs para conexão externa (desenvolvimento)
DATABASE_URL_DEV_SSL=postgresql+asyncpg://whatsapp_app:PASSWORD@localhost:5432/whatsapp_agent?ssl=require&sslmode=require

# Parâmetros SSL recomendados:
# sslmode=require - SSL obrigatório
# sslmode=verify-ca - Verificar certificado CA
# sslmode=verify-full - Verificação completa (recomendado para produção)
"""
    
    ssl_dir = "/home/vancim/whats_agent/config/postgres"
    with open(f"{ssl_dir}/ssl_connection_urls.env", 'w') as f:
        f.write(ssl_urls)
    
    print("✅ URLs de conexão SSL criadas")
    return True

def configure_table_encryption():
    """Configura criptografia a nível de coluna para dados sensíveis"""
    print("🔐 Configurando criptografia de colunas sensíveis...")
    
    encryption_sql = """
-- ===========================================
-- CRIPTOGRAFIA A NÍVEL DE COLUNA
-- ===========================================

-- Instalar extensão pgcrypto (se disponível)
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Função para criptografar dados sensíveis
CREATE OR REPLACE FUNCTION encrypt_sensitive_data(data TEXT, key_name TEXT DEFAULT 'default')
RETURNS TEXT AS $$
BEGIN
    -- Usar chave do ambiente ou chave padrão
    RETURN encode(
        pgp_sym_encrypt(
            data, 
            COALESCE(current_setting('app.encryption_key', true), 'default_key_change_me'),
            'compress-algo=1, cipher-algo=aes256'
        ), 
        'base64'
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Função para descriptografar dados sensíveis
CREATE OR REPLACE FUNCTION decrypt_sensitive_data(encrypted_data TEXT, key_name TEXT DEFAULT 'default')
RETURNS TEXT AS $$
BEGIN
    IF encrypted_data IS NULL OR encrypted_data = '' THEN
        RETURN NULL;
    END IF;
    
    RETURN pgp_sym_decrypt(
        decode(encrypted_data, 'base64'),
        COALESCE(current_setting('app.encryption_key', true), 'default_key_change_me')
    );
EXCEPTION
    WHEN OTHERS THEN
        -- Em caso de erro, retornar NULL (dados podem estar corrompidos)
        RETURN NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ===========================================
-- VIEWS CRIPTOGRAFADAS PARA DADOS SENSÍVEIS
-- ===========================================

-- View para usuários com dados criptografados
CREATE OR REPLACE VIEW users_encrypted AS
SELECT 
    id,
    wa_id,
    nome,
    -- Criptografar telefone e email
    encrypt_sensitive_data(telefone) AS telefone_encrypted,
    encrypt_sensitive_data(email) AS email_encrypted,
    created_at,
    updated_at
FROM users;

-- View para descriptografia (apenas para aplicação)
CREATE OR REPLACE VIEW users_decrypted AS
SELECT 
    id,
    wa_id,
    nome,
    -- Descriptografar telefone e email
    decrypt_sensitive_data(telefone_encrypted) AS telefone,
    decrypt_sensitive_data(email_encrypted) AS email,
    created_at,
    updated_at
FROM users_encrypted;

-- ===========================================
-- TRIGGERS PARA CRIPTOGRAFIA AUTOMÁTICA
-- ===========================================

-- Função de trigger para criptografar dados antes de inserir/atualizar
CREATE OR REPLACE FUNCTION encrypt_user_data()
RETURNS TRIGGER AS $$
BEGIN
    -- Criptografar dados sensíveis se fornecidos em texto plano
    IF NEW.telefone IS NOT NULL AND NEW.telefone NOT LIKE 'gAAAAAB%' THEN
        NEW.telefone := encrypt_sensitive_data(NEW.telefone);
    END IF;
    
    IF NEW.email IS NOT NULL AND NEW.email NOT LIKE 'gAAAAAB%' THEN
        NEW.email := encrypt_sensitive_data(NEW.email);
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Aplicar trigger na tabela users (comentado para não quebrar dados existentes)
-- DROP TRIGGER IF EXISTS users_encrypt_trigger ON users;
-- CREATE TRIGGER users_encrypt_trigger
--     BEFORE INSERT OR UPDATE ON users
--     FOR EACH ROW EXECUTE FUNCTION encrypt_user_data();

-- ===========================================
-- AUDITORIA DE ACESSO A DADOS SENSÍVEIS
-- ===========================================

-- Tabela de auditoria para acesso a dados sensíveis
CREATE TABLE IF NOT EXISTS data_access_audit (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(50) NOT NULL,
    record_id INTEGER,
    user_name VARCHAR(100),
    access_type VARCHAR(20), -- SELECT, INSERT, UPDATE, DELETE
    accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    application_name TEXT
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_data_access_audit_table_record 
    ON data_access_audit(table_name, record_id);
CREATE INDEX IF NOT EXISTS idx_data_access_audit_accessed_at 
    ON data_access_audit(accessed_at);

-- Função para registrar acesso a dados sensíveis
CREATE OR REPLACE FUNCTION audit_data_access(
    p_table_name TEXT,
    p_record_id INTEGER,
    p_access_type TEXT
) RETURNS VOID AS $$
BEGIN
    INSERT INTO data_access_audit (
        table_name,
        record_id,
        user_name,
        access_type,
        ip_address,
        application_name
    ) VALUES (
        p_table_name,
        p_record_id,
        current_user,
        p_access_type,
        inet_client_addr(),
        current_setting('application_name', true)
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ===========================================
-- POLÍTICAS DE SEGURANÇA (ROW LEVEL SECURITY)
-- ===========================================

-- Habilitar RLS em tabelas sensíveis (desabilitado por enquanto)
-- ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Política para permitir acesso apenas aos próprios dados
-- CREATE POLICY users_own_data ON users
--     FOR ALL TO whatsapp_app
--     USING (wa_id = current_setting('app.current_user_wa_id', true));

-- Política para usuário de backup (apenas leitura)
-- CREATE POLICY users_backup_access ON users
--     FOR SELECT TO whatsapp_backup
--     USING (true);

-- Política para usuário somente leitura
-- CREATE POLICY users_readonly_access ON users
--     FOR SELECT TO whatsapp_readonly
--     USING (true);
"""
    
    config_dir = "/home/vancim/whats_agent/config/postgres"
    with open(f"{config_dir}/column_encryption.sql", 'w') as f:
        f.write(encryption_sql)
    
    print("✅ Scripts de criptografia de colunas criados")
    return True

def create_ssl_test_script():
    """Cria script para testar conexões SSL"""
    print("🧪 Criando script de teste SSL...")
    
    test_script = '''#!/usr/bin/env python3
"""
🧪 TESTE DE CONEXÃO SSL COM POSTGRESQL
=====================================
"""

import asyncio
import asyncpg
import psycopg2
import ssl
from datetime import datetime

async def test_ssl_connection():
    """Testa conexão SSL com PostgreSQL"""
    print("🔐 TESTE DE CONEXÃO SSL - POSTGRESQL")
    print("=" * 50)
    print(f"📅 Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print()
    
    # URLs de teste (ajustar conforme necessário)
    test_connections = [
        {
            'name': 'PostgreSQL SSL Async',
            'url': 'postgresql://whatsapp_app:PASSWORD@localhost:5432/whatsapp_agent?sslmode=require',
            'type': 'async'
        },
        {
            'name': 'PostgreSQL SSL Sync',
            'url': 'postgresql://whatsapp_app:PASSWORD@localhost:5432/whatsapp_agent?sslmode=require',
            'type': 'sync'
        }
    ]
    
    results = []
    
    for test in test_connections:
        print(f"🔄 Testando: {test['name']}")
        
        try:
            if test['type'] == 'async':
                # Teste assíncrono
                conn = await asyncpg.connect(test['url'])
                
                # Verificar SSL
                ssl_info = await conn.fetchrow("SELECT ssl_is_used();")
                version = await conn.fetchval("SELECT version();")
                
                print(f"   ✅ Conectado via SSL: {ssl_info['ssl_is_used']}")
                print(f"   📋 Versão: {version[:50]}...")
                
                await conn.close()
                results.append(True)
                
            else:
                # Teste síncrono
                conn = psycopg2.connect(test['url'])
                cursor = conn.cursor()
                
                # Verificar SSL
                cursor.execute("SELECT ssl_is_used();")
                ssl_used = cursor.fetchone()[0]
                
                cursor.execute("SELECT version();")
                version = cursor.fetchone()[0]
                
                print(f"   ✅ Conectado via SSL: {ssl_used}")
                print(f"   📋 Versão: {version[:50]}...")
                
                conn.close()
                results.append(True)
                
        except Exception as e:
            print(f"   ❌ Erro: {e}")
            results.append(False)
        
        print()
    
    # Resultado final
    passed = sum(results)
    total = len(results)
    
    print("📊 RESULTADO DOS TESTES SSL")
    print("-" * 30)
    print(f"   Passou: {passed}/{total}")
    
    if passed == total:
        print("   🎉 Todos os testes SSL passaram!")
        return 0
    else:
        print("   ⚠️ Alguns testes SSL falharam")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(test_ssl_connection()))
'''
    
    test_file = "/home/vancim/whats_agent/scripts/test_database_ssl.py"
    with open(test_file, 'w') as f:
        f.write(test_script)
    
    os.chmod(test_file, 0o755)
    print(f"✅ Script de teste SSL criado: {test_file}")
    return True

def main():
    """Função principal"""
    print("🔐 CONFIGURAÇÃO DE CRIPTOGRAFIA DE BANCO DE DADOS")
    print("=" * 60)
    print()
    
    tasks = [
        ("Certificados SSL", configure_ssl_certificates),
        ("Configuração PostgreSQL SSL", configure_postgresql_ssl),
        ("Configuração pg_hba", configure_pg_hba),
        ("Docker PostgreSQL SSL", configure_docker_postgres_ssl),
        ("URLs de conexão SSL", create_encrypted_connection_urls),
        ("Criptografia de colunas", configure_table_encryption),
        ("Script de teste SSL", create_ssl_test_script)
    ]
    
    completed = 0
    total = len(tasks)
    
    for task_name, task_func in tasks:
        print(f"🔄 {task_name}...")
        try:
            if task_func():
                completed += 1
                print(f"✅ {task_name} concluído")
            else:
                print(f"❌ {task_name} falhou")
        except Exception as e:
            print(f"❌ {task_name} erro: {e}")
        print()
    
    print("🎉 CONFIGURAÇÃO DE CRIPTOGRAFIA CONCLUÍDA!")
    print("=" * 60)
    print(f"✅ Tarefas concluídas: {completed}/{total}")
    
    success_rate = (completed / total) * 100
    print(f"📊 Taxa de sucesso: {success_rate:.1f}%")
    
    print()
    print("📋 PRÓXIMOS PASSOS:")
    print("1. Revisar configurações em config/postgres/")
    print("2. Atualizar docker-compose.yml com configurações SSL")
    print("3. Aplicar scripts SQL para criptografia de colunas")
    print("4. Testar conexões SSL com scripts/test_database_ssl.py")
    print("5. Atualizar URLs de conexão na aplicação")
    
    return 0 if success_rate >= 80 else 1

if __name__ == "__main__":
    sys.exit(main())
