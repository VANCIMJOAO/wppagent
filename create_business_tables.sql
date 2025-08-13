-- Criação das tabelas de negócio faltantes
-- WhatsApp Agent - Business Tables

-- 1. Verificar se a tabela business_hours existe, se não, criar
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'business_hours') THEN
        CREATE TABLE business_hours (
            id SERIAL PRIMARY KEY,
            business_id INTEGER NOT NULL,
            day_of_week INTEGER NOT NULL CHECK (day_of_week >= 0 AND day_of_week <= 6),
            is_open BOOLEAN NOT NULL DEFAULT true,
            open_time TIME,
            close_time TIME,
            break_start_time TIME,
            break_end_time TIME,
            notes TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
            FOREIGN KEY (business_id) REFERENCES businesses(id)
        );
        CREATE INDEX idx_business_hours_business_day ON business_hours(business_id, day_of_week);
        
        -- Inserir dados iniciais (segunda a sexta 9h-18h)
        INSERT INTO business_hours (business_id, day_of_week, is_open, open_time, close_time, notes) VALUES
        (1, 0, false, null, null, 'Fechado aos domingos'),
        (1, 1, true, '09:00:00', '18:00:00', 'Segunda-feira'),
        (1, 2, true, '09:00:00', '18:00:00', 'Terça-feira'),
        (1, 3, true, '09:00:00', '18:00:00', 'Quarta-feira'),
        (1, 4, true, '09:00:00', '18:00:00', 'Quinta-feira'),
        (1, 5, true, '09:00:00', '18:00:00', 'Sexta-feira'),
        (1, 6, false, null, null, 'Fechado aos sábados');
        
        RAISE NOTICE 'Tabela business_hours criada com sucesso!';
    ELSE
        RAISE NOTICE 'Tabela business_hours já existe.';
    END IF;
END
$$;

-- 2. Verificar se a tabela payment_methods existe, se não, criar
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'payment_methods') THEN
        CREATE TABLE payment_methods (
            id SERIAL PRIMARY KEY,
            business_id INTEGER NOT NULL,
            name VARCHAR(100) NOT NULL,
            is_active BOOLEAN NOT NULL DEFAULT true,
            description TEXT,
            additional_info TEXT,
            display_order INTEGER DEFAULT 0,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
            FOREIGN KEY (business_id) REFERENCES businesses(id)
        );
        CREATE INDEX idx_payment_methods_business ON payment_methods(business_id, is_active);
        
        -- Inserir formas de pagamento padrão
        INSERT INTO payment_methods (business_id, name, description, display_order, is_active) VALUES
        (1, 'Dinheiro', 'Pagamento em espécie', 1, true),
        (1, 'PIX', 'Transferência instantânea', 2, true),
        (1, 'Cartão de Débito', 'Cartão de débito', 3, true),
        (1, 'Cartão de Crédito', 'Cartão de crédito', 4, true);
        
        RAISE NOTICE 'Tabela payment_methods criada com sucesso!';
    ELSE
        RAISE NOTICE 'Tabela payment_methods já existe.';
    END IF;
END
$$;

-- 3. Verificar se a tabela business_policies existe, se não, criar
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'business_policies') THEN
        CREATE TABLE business_policies (
            id SERIAL PRIMARY KEY,
            business_id INTEGER NOT NULL,
            policy_type VARCHAR(50) NOT NULL,
            title VARCHAR(200) NOT NULL,
            description TEXT NOT NULL,
            rules JSON,
            is_active BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
            FOREIGN KEY (business_id) REFERENCES businesses(id)
        );
        CREATE INDEX idx_business_policies_business_type ON business_policies(business_id, policy_type, is_active);
        
        -- Inserir políticas padrão
        INSERT INTO business_policies (business_id, policy_type, title, description, rules, is_active) VALUES
        (1, 'cancellation', 'Política de Cancelamento', 'Cancelamentos devem ser feitos com pelo menos 24 horas de antecedência.', '{"min_hours": 24, "refund": false}', true),
        (1, 'rescheduling', 'Política de Reagendamento', 'Reagendamentos podem ser feitos até 2 horas antes do horário marcado.', '{"min_hours": 2, "max_reschedules": 2}', true),
        (1, 'no_show', 'Política de Falta', 'Faltas sem aviso prévio resultam em cobrança de taxa.', '{"fee_percentage": 50, "grace_period": 15}', true);
        
        RAISE NOTICE 'Tabela business_policies criada com sucesso!';
    ELSE
        RAISE NOTICE 'Tabela business_policies já existe.';
    END IF;
END
$$;
