#!/usr/bin/env python3
"""
🔧 CORREÇÃO E VALIDAÇÃO DE CONSTRAINTS DO BANCO
=============================================

Analisa e corrige constraints do banco de dados para máxima integridade
"""

import os
import sys
import asyncio
import asyncpg
from datetime import datetime
from pathlib import Path

# Adicionar o diretório da aplicação ao path
sys.path.append('/home/vancim/whats_agent')

async def analyze_current_constraints(conn):
    """Analisa constraints atuais do banco"""
    print("🔍 Analisando constraints atuais...")
    
    # Consultar constraints existentes
    query = """
    SELECT 
        tc.table_name,
        tc.constraint_name,
        tc.constraint_type,
        kcu.column_name,
        ccu.table_name AS foreign_table_name,
        ccu.column_name AS foreign_column_name,
        rc.update_rule,
        rc.delete_rule
    FROM information_schema.table_constraints tc
    LEFT JOIN information_schema.key_column_usage kcu 
        ON tc.constraint_name = kcu.constraint_name
        AND tc.table_schema = kcu.table_schema
    LEFT JOIN information_schema.constraint_column_usage ccu 
        ON ccu.constraint_name = tc.constraint_name
        AND ccu.table_schema = tc.table_schema
    LEFT JOIN information_schema.referential_constraints rc 
        ON rc.constraint_name = tc.constraint_name
        AND rc.constraint_schema = tc.table_schema
    WHERE tc.table_schema = 'public'
    ORDER BY tc.table_name, tc.constraint_type;
    """
    
    constraints = await conn.fetch(query)
    
    print(f"📊 Encontradas {len(constraints)} constraints")
    
    # Organizar por tipo
    by_type = {}
    for constraint in constraints:
        constraint_type = constraint['constraint_type']
        if constraint_type not in by_type:
            by_type[constraint_type] = []
        by_type[constraint_type].append(constraint)
    
    for constraint_type, items in by_type.items():
        print(f"   {constraint_type}: {len(items)}")
    
    return constraints

async def apply_database_constraints(conn):
    """Aplica constraints de integridade melhoradas"""
    print("🔧 Aplicando constraints de integridade...")
    
    constraints_sql = """
    -- ===========================================
    -- CONSTRAINTS DE INTEGRIDADE DE DADOS
    -- ===========================================
    
    -- 1. TABELA USERS
    -- Constraints básicas
    ALTER TABLE users DROP CONSTRAINT IF EXISTS users_wa_id_length;
    ALTER TABLE users ADD CONSTRAINT users_wa_id_length 
        CHECK (char_length(wa_id) >= 10 AND char_length(wa_id) <= 50);
    
    ALTER TABLE users DROP CONSTRAINT IF EXISTS users_telefone_format;
    ALTER TABLE users ADD CONSTRAINT users_telefone_format 
        CHECK (telefone ~ '^[0-9+\-\s()]+$' OR telefone IS NULL);
    
    ALTER TABLE users DROP CONSTRAINT IF EXISTS users_email_format;
    ALTER TABLE users ADD CONSTRAINT users_email_format 
        CHECK (email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$' OR email IS NULL);
    
    ALTER TABLE users DROP CONSTRAINT IF EXISTS users_nome_not_empty;
    ALTER TABLE users ADD CONSTRAINT users_nome_not_empty 
        CHECK (nome IS NULL OR char_length(trim(nome)) > 0);
    
    -- 2. TABELA ADMIN_USERS
    -- Constraints de segurança
    ALTER TABLE admin_users DROP CONSTRAINT IF EXISTS admin_users_username_length;
    ALTER TABLE admin_users ADD CONSTRAINT admin_users_username_length 
        CHECK (char_length(username) >= 3 AND char_length(username) <= 50);
    
    ALTER TABLE admin_users DROP CONSTRAINT IF EXISTS admin_users_username_format;
    ALTER TABLE admin_users ADD CONSTRAINT admin_users_username_format 
        CHECK (username ~ '^[a-zA-Z0-9_.-]+$');
    
    ALTER TABLE admin_users DROP CONSTRAINT IF EXISTS admin_users_email_format;
    ALTER TABLE admin_users ADD CONSTRAINT admin_users_email_format 
        CHECK (email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$');
    
    ALTER TABLE admin_users DROP CONSTRAINT IF EXISTS admin_users_password_not_empty;
    ALTER TABLE admin_users ADD CONSTRAINT admin_users_password_not_empty 
        CHECK (char_length(password_hash) >= 50);
    
    -- 3. TABELA CONVERSATIONS
    -- Constraints de status
    ALTER TABLE conversations DROP CONSTRAINT IF EXISTS conversations_status_valid;
    ALTER TABLE conversations ADD CONSTRAINT conversations_status_valid 
        CHECK (status IN ('active', 'human', 'closed', 'waiting', 'escalated'));
    
    ALTER TABLE conversations DROP CONSTRAINT IF EXISTS conversations_dates_logical;
    ALTER TABLE conversations ADD CONSTRAINT conversations_dates_logical 
        CHECK (last_message_at >= created_at);
    
    -- 4. TABELA MESSAGES
    -- Constraints de conteúdo
    ALTER TABLE messages DROP CONSTRAINT IF EXISTS messages_type_valid;
    ALTER TABLE messages ADD CONSTRAINT messages_type_valid 
        CHECK (type IN ('text', 'image', 'audio', 'video', 'document', 'location', 'contact', 'sticker', 'reaction', 'interactive'));
    
    ALTER TABLE messages DROP CONSTRAINT IF EXISTS messages_direction_valid;
    ALTER TABLE messages ADD CONSTRAINT messages_direction_valid 
        CHECK (direction IN ('incoming', 'outgoing'));
    
    ALTER TABLE messages DROP CONSTRAINT IF EXISTS messages_content_not_empty;
    ALTER TABLE messages ADD CONSTRAINT messages_content_not_empty 
        CHECK (content IS NOT NULL AND char_length(trim(content)) > 0);
    
    ALTER TABLE messages DROP CONSTRAINT IF EXISTS messages_status_valid;
    ALTER TABLE messages ADD CONSTRAINT messages_status_valid 
        CHECK (status IN ('sent', 'delivered', 'read', 'failed', 'pending'));
    
    -- 5. TABELA APPOINTMENTS
    -- Constraints de agendamento
    ALTER TABLE appointments DROP CONSTRAINT IF EXISTS appointments_status_valid;
    ALTER TABLE appointments ADD CONSTRAINT appointments_status_valid 
        CHECK (status IN ('scheduled', 'confirmed', 'cancelled', 'completed', 'no_show', 'rescheduled'));
    
    ALTER TABLE appointments DROP CONSTRAINT IF EXISTS appointments_date_future;
    ALTER TABLE appointments ADD CONSTRAINT appointments_date_future 
        CHECK (appointment_date > created_at);
    
    ALTER TABLE appointments DROP CONSTRAINT IF EXISTS appointments_service_not_empty;
    ALTER TABLE appointments ADD CONSTRAINT appointments_service_not_empty 
        CHECK (service IS NULL OR char_length(trim(service)) > 0);
    
    -- 6. TABELA LOGIN_SESSIONS
    -- Constraints de sessão
    ALTER TABLE login_sessions DROP CONSTRAINT IF EXISTS login_sessions_token_length;
    ALTER TABLE login_sessions ADD CONSTRAINT login_sessions_token_length 
        CHECK (char_length(session_token) >= 32);
    
    ALTER TABLE login_sessions DROP CONSTRAINT IF EXISTS login_sessions_ip_format;
    ALTER TABLE login_sessions ADD CONSTRAINT login_sessions_ip_format 
        CHECK (ip_address ~ '^([0-9]{1,3}\.){3}[0-9]{1,3}$|^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$' OR ip_address IS NULL);
    
    ALTER TABLE login_sessions DROP CONSTRAINT IF EXISTS login_sessions_dates_logical;
    ALTER TABLE login_sessions ADD CONSTRAINT login_sessions_dates_logical 
        CHECK (expires_at > created_at);
    
    -- 7. TABELA ANALYTICS_EVENTS
    -- Constraints de eventos
    ALTER TABLE analytics_events DROP CONSTRAINT IF EXISTS analytics_events_event_type_not_empty;
    ALTER TABLE analytics_events ADD CONSTRAINT analytics_events_event_type_not_empty 
        CHECK (char_length(trim(event_type)) > 0);
    
    -- ===========================================
    -- FOREIGN KEY CONSTRAINTS COM CASCADE RULES
    -- ===========================================
    
    -- Verificar e recriar FKs com regras apropriadas
    ALTER TABLE conversations DROP CONSTRAINT IF EXISTS conversations_user_id_fkey;
    ALTER TABLE conversations ADD CONSTRAINT conversations_user_id_fkey 
        FOREIGN KEY (user_id) REFERENCES users(id) 
        ON DELETE CASCADE ON UPDATE CASCADE;
    
    ALTER TABLE messages DROP CONSTRAINT IF EXISTS messages_user_id_fkey;
    ALTER TABLE messages ADD CONSTRAINT messages_user_id_fkey 
        FOREIGN KEY (user_id) REFERENCES users(id) 
        ON DELETE CASCADE ON UPDATE CASCADE;
    
    ALTER TABLE messages DROP CONSTRAINT IF EXISTS messages_conversation_id_fkey;
    ALTER TABLE messages ADD CONSTRAINT messages_conversation_id_fkey 
        FOREIGN KEY (conversation_id) REFERENCES conversations(id) 
        ON DELETE CASCADE ON UPDATE CASCADE;
    
    ALTER TABLE appointments DROP CONSTRAINT IF EXISTS appointments_user_id_fkey;
    ALTER TABLE appointments ADD CONSTRAINT appointments_user_id_fkey 
        FOREIGN KEY (user_id) REFERENCES users(id) 
        ON DELETE CASCADE ON UPDATE CASCADE;
    
    ALTER TABLE login_sessions DROP CONSTRAINT IF EXISTS login_sessions_admin_user_id_fkey;
    ALTER TABLE login_sessions ADD CONSTRAINT login_sessions_admin_user_id_fkey 
        FOREIGN KEY (admin_user_id) REFERENCES admin_users(id) 
        ON DELETE CASCADE ON UPDATE CASCADE;
    
    -- ===========================================
    -- ÍNDICES PARA PERFORMANCE
    -- ===========================================
    
    -- Índices compostos para consultas frequentes
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_messages_user_conversation 
        ON messages(user_id, conversation_id);
    
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_messages_created_status 
        ON messages(created_at, status);
    
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversations_user_status 
        ON conversations(user_id, status);
    
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_appointments_user_date 
        ON appointments(user_id, appointment_date);
    
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_login_sessions_token_active 
        ON login_sessions(session_token, is_active);
    
    -- Índices parciais para consultas específicas
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_messages_pending 
        ON messages(created_at) WHERE status = 'pending';
    
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversations_active 
        ON conversations(last_message_at) WHERE status = 'active';
    
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_appointments_upcoming 
        ON appointments(appointment_date) WHERE status IN ('scheduled', 'confirmed');
    
    -- ===========================================
    -- TRIGGERS PARA AUDITORIA
    -- ===========================================
    
    -- Função para atualizar updated_at
    CREATE OR REPLACE FUNCTION update_updated_at_column()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = CURRENT_TIMESTAMP;
        RETURN NEW;
    END;
    $$ language 'plpgsql';
    
    -- Triggers para atualização automática de timestamps
    DROP TRIGGER IF EXISTS update_users_updated_at ON users;
    CREATE TRIGGER update_users_updated_at 
        BEFORE UPDATE ON users 
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    
    DROP TRIGGER IF EXISTS update_admin_users_updated_at ON admin_users;
    CREATE TRIGGER update_admin_users_updated_at 
        BEFORE UPDATE ON admin_users 
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    
    DROP TRIGGER IF EXISTS update_conversations_updated_at ON conversations;
    CREATE TRIGGER update_conversations_updated_at 
        BEFORE UPDATE ON conversations 
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    
    DROP TRIGGER IF EXISTS update_messages_updated_at ON messages;
    CREATE TRIGGER update_messages_updated_at 
        BEFORE UPDATE ON messages 
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    
    DROP TRIGGER IF EXISTS update_appointments_updated_at ON appointments;
    CREATE TRIGGER update_appointments_updated_at 
        BEFORE UPDATE ON appointments 
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    
    -- ===========================================
    -- SISTEMA DE AUDITORIA AVANÇADO
    -- ===========================================
    
    -- Tabela de auditoria para todas as operações
    CREATE TABLE IF NOT EXISTS audit_log (
        id SERIAL PRIMARY KEY,
        table_name VARCHAR(50) NOT NULL,
        record_id INTEGER,
        operation VARCHAR(10) NOT NULL, -- INSERT, UPDATE, DELETE
        old_values JSONB,
        new_values JSONB,
        user_name VARCHAR(100),
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        ip_address INET,
        application_name TEXT
    );
    
    -- Índices para performance da auditoria
    CREATE INDEX IF NOT EXISTS idx_audit_log_table_operation 
        ON audit_log(table_name, operation);
    CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp 
        ON audit_log(timestamp);
    CREATE INDEX IF NOT EXISTS idx_audit_log_user 
        ON audit_log(user_name);
    
    -- Função de auditoria genérica
    CREATE OR REPLACE FUNCTION audit_trigger_function()
    RETURNS TRIGGER AS $$
    BEGIN
        IF TG_OP = 'DELETE' THEN
            INSERT INTO audit_log (
                table_name, record_id, operation, old_values,
                user_name, ip_address, application_name
            ) VALUES (
                TG_TABLE_NAME, OLD.id, TG_OP, to_jsonb(OLD),
                current_user, inet_client_addr(), 
                current_setting('application_name', true)
            );
            RETURN OLD;
        ELSIF TG_OP = 'UPDATE' THEN
            INSERT INTO audit_log (
                table_name, record_id, operation, old_values, new_values,
                user_name, ip_address, application_name
            ) VALUES (
                TG_TABLE_NAME, NEW.id, TG_OP, to_jsonb(OLD), to_jsonb(NEW),
                current_user, inet_client_addr(), 
                current_setting('application_name', true)
            );
            RETURN NEW;
        ELSIF TG_OP = 'INSERT' THEN
            INSERT INTO audit_log (
                table_name, record_id, operation, new_values,
                user_name, ip_address, application_name
            ) VALUES (
                TG_TABLE_NAME, NEW.id, TG_OP, to_jsonb(NEW),
                current_user, inet_client_addr(), 
                current_setting('application_name', true)
            );
            RETURN NEW;
        END IF;
        RETURN NULL;
    END;
    $$ LANGUAGE plpgsql SECURITY DEFINER;
    
    -- Aplicar triggers de auditoria em tabelas principais
    DROP TRIGGER IF EXISTS audit_users ON users;
    CREATE TRIGGER audit_users
        AFTER INSERT OR UPDATE OR DELETE ON users
        FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();
    
    DROP TRIGGER IF EXISTS audit_conversations ON conversations;
    CREATE TRIGGER audit_conversations
        AFTER INSERT OR UPDATE OR DELETE ON conversations
        FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();
    
    DROP TRIGGER IF EXISTS audit_messages ON messages;
    CREATE TRIGGER audit_messages
        AFTER INSERT OR UPDATE OR DELETE ON messages
        FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();
    
    DROP TRIGGER IF EXISTS audit_appointments ON appointments;
    CREATE TRIGGER audit_appointments
        AFTER INSERT OR UPDATE OR DELETE ON appointments
        FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();
    
    -- ===========================================
    -- VIEWS DE SEGURANÇA
    -- ===========================================
    
    -- View segura para dados de usuários (sem informações sensíveis)
    CREATE OR REPLACE VIEW users_safe AS
    SELECT 
        id,
        wa_id,
        nome,
        LEFT(telefone, 3) || 'XXXXX' || RIGHT(telefone, 2) AS telefone_masked,
        CASE 
            WHEN email IS NOT NULL THEN 
                LEFT(email, 2) || 'XXX@' || SPLIT_PART(email, '@', 2)
            ELSE NULL 
        END AS email_masked,
        created_at,
        updated_at
    FROM users;
    
    -- View para estatísticas sem dados pessoais
    CREATE OR REPLACE VIEW user_stats AS
    SELECT 
        DATE_TRUNC('day', created_at) AS date,
        COUNT(*) AS new_users,
        COUNT(CASE WHEN telefone IS NOT NULL THEN 1 END) AS users_with_phone,
        COUNT(CASE WHEN email IS NOT NULL THEN 1 END) AS users_with_email
    FROM users
    GROUP BY DATE_TRUNC('day', created_at)
    ORDER BY date DESC;
    """
    
    # Dividir em comandos individuais para melhor controle de erros
    commands = [cmd.strip() for cmd in constraints_sql.split(';') if cmd.strip()]
    
    applied = 0
    errors = 0
    
    for i, command in enumerate(commands):
        if not command:
            continue
            
        try:
            await conn.execute(command)
            applied += 1
            if i % 10 == 0:  # Progress indicator
                print(f"   Aplicado {i}/{len(commands)} comandos...")
        except Exception as e:
            errors += 1
            print(f"   ⚠️ Erro no comando {i}: {str(e)[:100]}")
    
    print(f"✅ Aplicadas {applied} constraints, {errors} erros")
    return applied, errors

async def validate_constraints(conn):
    """Valida se as constraints estão funcionando"""
    print("🧪 Validando constraints aplicadas...")
    
    validations = [
        # Teste 1: wa_id length
        {
            'name': 'wa_id length constraint',
            'query': "INSERT INTO users (wa_id, nome) VALUES ('123', 'Test')",
            'should_fail': True
        },
        # Teste 2: email format
        {
            'name': 'email format constraint',
            'query': "INSERT INTO users (wa_id, email) VALUES ('1234567890', 'invalid-email')",
            'should_fail': True
        },
        # Teste 3: valid data
        {
            'name': 'valid user insertion',
            'query': "INSERT INTO users (wa_id, nome, email) VALUES ('test123456', 'Test User', 'test@example.com')",
            'should_fail': False,
            'cleanup': "DELETE FROM users WHERE wa_id = 'test123456'"
        },
        # Teste 4: conversation status
        {
            'name': 'invalid conversation status',
            'query': "INSERT INTO conversations (user_id, status) VALUES (1, 'invalid_status')",
            'should_fail': True
        }
    ]
    
    passed = 0
    total = len(validations)
    
    for validation in validations:
        try:
            await conn.execute(validation['query'])
            
            if validation['should_fail']:
                print(f"   ❌ {validation['name']}: Deveria ter falhado mas passou")
            else:
                print(f"   ✅ {validation['name']}: Passou corretamente")
                passed += 1
                
                # Cleanup se necessário
                if 'cleanup' in validation:
                    await conn.execute(validation['cleanup'])
                    
        except Exception as e:
            if validation['should_fail']:
                print(f"   ✅ {validation['name']}: Falhou corretamente")
                passed += 1
            else:
                print(f"   ❌ {validation['name']}: Falhou inesperadamente: {e}")
    
    print(f"📊 Validações: {passed}/{total} passaram")
    return passed, total

async def generate_constraints_report(conn):
    """Gera relatório de constraints"""
    print("📊 Gerando relatório de constraints...")
    
    # Consultar constraints finais
    constraints = await analyze_current_constraints(conn)
    
    # Estatísticas por tabela
    table_stats = {}
    for constraint in constraints:
        table = constraint['table_name']
        if table not in table_stats:
            table_stats[table] = {
                'PRIMARY KEY': 0,
                'FOREIGN KEY': 0,
                'CHECK': 0,
                'UNIQUE': 0
            }
        
        constraint_type = constraint['constraint_type']
        if constraint_type in table_stats[table]:
            table_stats[table][constraint_type] += 1
    
    report = []
    report.append("🔧 RELATÓRIO DE CONSTRAINTS DO BANCO DE DADOS")
    report.append("=" * 60)
    report.append(f"📅 Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    report.append("")
    
    report.append("📊 ESTATÍSTICAS POR TABELA")
    report.append("-" * 40)
    
    for table, stats in table_stats.items():
        report.append(f"📋 {table}:")
        for constraint_type, count in stats.items():
            if count > 0:
                report.append(f"   {constraint_type}: {count}")
        report.append("")
    
    report.append("🔍 CONSTRAINTS DETALHADAS")
    report.append("-" * 40)
    
    current_table = None
    for constraint in constraints:
        if constraint['table_name'] != current_table:
            current_table = constraint['table_name']
            report.append(f"\n📋 {current_table}:")
        
        constraint_info = f"   {constraint['constraint_type']}: {constraint['constraint_name']}"
        if constraint['column_name']:
            constraint_info += f" ({constraint['column_name']})"
        if constraint['foreign_table_name']:
            constraint_info += f" -> {constraint['foreign_table_name']}.{constraint['foreign_column_name']}"
        
        report.append(constraint_info)
    
    # Salvar relatório
    report_content = "\n".join(report)
    report_file = f"/home/vancim/whats_agent/reports/database_constraints_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    os.makedirs(os.path.dirname(report_file), exist_ok=True)
    with open(report_file, 'w') as f:
        f.write(report_content)
    
    print(f"📄 Relatório salvo em: {report_file}")
    return report_content

async def main():
    """Função principal"""
    print("🔧 CORREÇÃO DE CONSTRAINTS DO BANCO DE DADOS")
    print("=" * 60)
    print()
    
    # Conectar ao banco
    try:
        # Usar credenciais do .env atual
        from app.config import settings
        conn = await asyncpg.connect(settings.database_url.replace('postgresql+asyncpg://', 'postgresql://'))
        print("✅ Conectado ao banco de dados")
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        return 1
    
    try:
        # Análise inicial
        await analyze_current_constraints(conn)
        print()
        
        # Aplicar constraints
        applied, errors = await apply_database_constraints(conn)
        print()
        
        # Validar constraints
        passed, total = await validate_constraints(conn)
        print()
        
        # Gerar relatório
        await generate_constraints_report(conn)
        
        print()
        print("🎉 CORREÇÃO DE CONSTRAINTS CONCLUÍDA!")
        print("=" * 50)
        print(f"✅ Constraints aplicadas: {applied}")
        print(f"⚠️ Erros encontrados: {errors}")
        print(f"🧪 Validações passaram: {passed}/{total}")
        
        success_rate = (applied / (applied + errors)) * 100 if (applied + errors) > 0 else 0
        print(f"📊 Taxa de sucesso: {success_rate:.1f}%")
        
        if success_rate >= 90:
            print("🏆 Excelente - Banco de dados com integridade máxima!")
            return 0
        elif success_rate >= 70:
            print("✅ Bom - Constraints aplicadas com sucesso")
            return 0
        else:
            print("⚠️ Atenção - Algumas constraints falharam")
            return 1
            
    finally:
        await conn.close()

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
