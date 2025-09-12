-- H004: Remover tabela admins órfã
-- Data: 2025-09-11
-- Prioridade: 🟡 MÉDIA
-- 
-- PROBLEMA: Tabela admins órfã vazia após migração H002
-- SOLUÇÃO: Remover tabela admins e sequência associada
-- 
-- VALIDAÇÕES PRÉ-MIGRAÇÃO:
-- ✅ Tabela admins vazia (0 registros)
-- ✅ Tabela admin_users ativa (3 registros)
-- ✅ Nenhuma foreign key dependente
-- ✅ Sistema admin funcional
-- ✅ Backup realizado em H004_BACKUP_ADMINS_TABLE.sql

BEGIN;

-- Log da migração
DO $$
BEGIN
    RAISE NOTICE 'H004: Iniciando remoção da tabela admins órfã';
    RAISE NOTICE 'H004: Backup salvo em H004_BACKUP_ADMINS_TABLE.sql';
END $$;

-- Verificação final de segurança
DO $$
DECLARE
    admin_count INTEGER;
    admin_users_count INTEGER;
    fk_count INTEGER;
BEGIN
    -- Verificar se tabela admins está realmente vazia
    SELECT COUNT(*) INTO admin_count FROM admins;
    
    -- Verificar se admin_users tem registros
    SELECT COUNT(*) INTO admin_users_count FROM admin_users;
    
    -- Verificar foreign keys
    SELECT COUNT(*) INTO fk_count
    FROM information_schema.table_constraints AS tc 
    JOIN information_schema.key_column_usage AS kcu
        ON tc.constraint_name = kcu.constraint_name
    JOIN information_schema.constraint_column_usage AS ccu
        ON ccu.constraint_name = tc.constraint_name
    WHERE tc.constraint_type = 'FOREIGN KEY' 
        AND (ccu.table_name = 'admins' OR tc.table_name = 'admins');
    
    -- Validações
    IF admin_count > 0 THEN
        RAISE EXCEPTION 'H004: ERRO - Tabela admins não está vazia (% registros)', admin_count;
    END IF;
    
    IF admin_users_count = 0 THEN
        RAISE EXCEPTION 'H004: ERRO - Tabela admin_users está vazia. Sistema admin ficará sem funcionamento';
    END IF;
    
    IF fk_count > 0 THEN
        RAISE EXCEPTION 'H004: ERRO - Existem foreign keys dependentes (% encontradas)', fk_count;
    END IF;
    
    RAISE NOTICE 'H004: ✅ Validações passaram - Seguro para remoção';
    RAISE NOTICE 'H004: - admins: % registros', admin_count;
    RAISE NOTICE 'H004: - admin_users: % registros', admin_users_count;
    RAISE NOTICE 'H004: - foreign keys: % dependências', fk_count;
END $$;

-- Remover tabela admins
DROP TABLE IF EXISTS admins CASCADE;

-- Log da remoção da tabela
DO $$
BEGIN
    RAISE NOTICE 'H004: ✅ Tabela admins removida';
END $$;

-- Remover sequência associada
DROP SEQUENCE IF EXISTS admins_id_seq CASCADE;

-- Log da remoção da sequência
DO $$
BEGIN
    RAISE NOTICE 'H004: ✅ Sequência admins_id_seq removida';
END $$;

-- Verificação final
DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'admins') THEN
        RAISE EXCEPTION 'H004: ERRO - Tabela admins ainda existe após remoção';
    END IF;
    
    IF EXISTS (SELECT FROM information_schema.sequences WHERE sequence_name = 'admins_id_seq') THEN
        RAISE EXCEPTION 'H004: ERRO - Sequência admins_id_seq ainda existe após remoção';
    END IF;
    
    RAISE NOTICE 'H004: ✅ Remoção concluída com sucesso';
    RAISE NOTICE 'H004: ✅ Sistema admin continua funcional via admin_users';
END $$;

COMMIT;

-- Log final
DO $$
BEGIN
    RAISE NOTICE '==================================================';
    RAISE NOTICE 'H004: MIGRAÇÃO CONCLUÍDA COM SUCESSO';
    RAISE NOTICE '- Tabela admins órfã removida';
    RAISE NOTICE '- Sistema admin funcional via admin_users';
    RAISE NOTICE '- Backup disponível em H004_BACKUP_ADMINS_TABLE.sql';
    RAISE NOTICE '==================================================';
END $$;
