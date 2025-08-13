
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
