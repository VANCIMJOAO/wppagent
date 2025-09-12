-- H004: BACKUP da tabela admins órfã antes da remoção
-- Data: 2025-09-11
-- Motivo: Tabela admins está vazia e órfã após migração H002
-- Status: Sistema admin funciona via admin_users (3 registros)

-- ESTRUTURA ORIGINAL DA TABELA ADMINS:
/*
CREATE TABLE admins (
    id INTEGER NOT NULL DEFAULT nextval('admins_id_seq'::regclass),
    username VARCHAR(50) NOT NULL,
    email VARCHAR(255) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    CONSTRAINT admins_pkey PRIMARY KEY (id),
    CONSTRAINT admins_username_key UNIQUE (username),
    CONSTRAINT admins_email_key UNIQUE (email)
);

-- ÍNDICES:
CREATE UNIQUE INDEX admins_pkey ON public.admins USING btree (id);
CREATE UNIQUE INDEX admins_username_key ON public.admins USING btree (username);
CREATE UNIQUE INDEX admins_email_key ON public.admins USING btree (email);
CREATE INDEX ix_admins_id ON public.admins USING btree (id);

-- SEQUÊNCIA:
CREATE SEQUENCE admins_id_seq;
*/

-- DADOS: 0 registros (tabela vazia)
-- DEPENDÊNCIAS: Nenhuma foreign key dependente

-- VALIDAÇÃO ANTES DA REMOÇÃO:
-- ✅ admin_users: 3 registros ativos
-- ✅ Sistema admin funcional
-- ✅ Nenhuma dependência
-- ✅ Tabela vazia

-- COMANDO DE RESTAURAÇÃO (se necessário):
/*
-- Para restaurar a tabela (não recomendado):
CREATE SEQUENCE IF NOT EXISTS admins_id_seq;
CREATE TABLE IF NOT EXISTS admins (
    id INTEGER NOT NULL DEFAULT nextval('admins_id_seq'::regclass),
    username VARCHAR(50) NOT NULL,
    email VARCHAR(255) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    CONSTRAINT admins_pkey PRIMARY KEY (id),
    CONSTRAINT admins_username_key UNIQUE (username),
    CONSTRAINT admins_email_key UNIQUE (email)
);
CREATE INDEX IF NOT EXISTS ix_admins_id ON public.admins USING btree (id);
*/
