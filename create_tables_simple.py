#!/usr/bin/env python3
"""
Script SIMPLES para criar tabelas faltantes
Railway - Execução via Python puro
"""

import asyncio
import asyncpg
import os
import sys

# Configurações do banco (usar PUBLIC URL para acesso externo)
DATABASE_URL = os.getenv(
    'DATABASE_PUBLIC_URL', 
    'postgresql://postgres:UGARTPCwAADBBeBLctoRnQXLsoUvLJxz@caboose.proxy.rlwy.net:13910/railway'
)

async def create_missing_tables():
    """Criar tabelas faltantes no banco do Railway"""
    print("🔧 CRIANDO TABELAS FALTANTES NO RAILWAY")
    print("=" * 50)
    
    try:
        # Conectar ao banco
        conn = await asyncpg.connect(DATABASE_URL)
        print("✅ Conectado ao banco de dados!")
        
        # Verificar tabelas existentes
        existing_tables = await conn.fetch(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
        )
        table_names = [row[0] for row in existing_tables]
        print(f"📋 Tabelas existentes: {table_names}")
        
        # ========================================
        # 1. CRIAR TABELA BUSINESS_HOURS
        # ========================================
        if 'business_hours' not in table_names:
            print("🔧 Criando tabela business_hours...")
            await conn.execute('''
                CREATE TABLE business_hours (
                    id SERIAL PRIMARY KEY,
                    business_id INTEGER NOT NULL DEFAULT 1,
                    day_of_week INTEGER NOT NULL CHECK (day_of_week >= 0 AND day_of_week <= 6),
                    is_open BOOLEAN NOT NULL DEFAULT true,
                    open_time TIME,
                    close_time TIME,
                    break_start_time TIME,
                    break_end_time TIME,
                    notes TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
                );
            ''')
            
            await conn.execute('''
                CREATE INDEX idx_business_hours_business_day 
                ON business_hours(business_id, day_of_week);
            ''')
            
            # Inserir dados iniciais - usando SQL direto para TIME
            await conn.execute('''
                INSERT INTO business_hours (business_id, day_of_week, is_open, open_time, close_time, notes) VALUES
                (1, 0, false, NULL, NULL, 'Fechado aos domingos'),
                (1, 1, true, '09:00:00'::time, '18:00:00'::time, 'Segunda-feira'),
                (1, 2, true, '09:00:00'::time, '18:00:00'::time, 'Terça-feira'),
                (1, 3, true, '09:00:00'::time, '18:00:00'::time, 'Quarta-feira'),
                (1, 4, true, '09:00:00'::time, '18:00:00'::time, 'Quinta-feira'),
                (1, 5, true, '09:00:00'::time, '18:00:00'::time, 'Sexta-feira'),
                (1, 6, false, NULL, NULL, 'Fechado aos sábados')
            ''')
            
            print("✅ Tabela business_hours criada e populada!")
        else:
            print("✅ Tabela business_hours já existe")
        
        # ========================================
        # 2. CRIAR TABELA PAYMENT_METHODS
        # ========================================
        if 'payment_methods' not in table_names:
            print("🔧 Criando tabela payment_methods...")
            await conn.execute('''
                CREATE TABLE payment_methods (
                    id SERIAL PRIMARY KEY,
                    business_id INTEGER NOT NULL DEFAULT 1,
                    name VARCHAR(100) NOT NULL,
                    is_active BOOLEAN NOT NULL DEFAULT true,
                    description TEXT,
                    additional_info TEXT,
                    display_order INTEGER DEFAULT 0,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
                );
            ''')
            
            await conn.execute('''
                CREATE INDEX idx_payment_methods_business 
                ON payment_methods(business_id, is_active);
            ''')
            
            # Inserir dados iniciais
            payment_methods = [
                (1, 'Dinheiro', 'Pagamento em espécie', 1),
                (1, 'PIX', 'Transferência instantânea', 2),
                (1, 'Cartão de Débito', 'Cartão de débito', 3),
                (1, 'Cartão de Crédito', 'Cartão de crédito', 4)
            ]
            
            for data in payment_methods:
                await conn.execute('''
                    INSERT INTO payment_methods (business_id, name, description, display_order, is_active)
                    VALUES ($1, $2, $3, $4, true)
                ''', *data)
            
            print("✅ Tabela payment_methods criada e populada!")
        else:
            print("✅ Tabela payment_methods já existe")
        
        # ========================================
        # 3. CRIAR TABELA BUSINESS_POLICIES
        # ========================================
        if 'business_policies' not in table_names:
            print("🔧 Criando tabela business_policies...")
            await conn.execute('''
                CREATE TABLE business_policies (
                    id SERIAL PRIMARY KEY,
                    business_id INTEGER NOT NULL DEFAULT 1,
                    policy_type VARCHAR(50) NOT NULL,
                    title VARCHAR(200) NOT NULL,
                    description TEXT NOT NULL,
                    rules JSON,
                    is_active BOOLEAN NOT NULL DEFAULT true,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
                );
            ''')
            
            await conn.execute('''
                CREATE INDEX idx_business_policies_business_type 
                ON business_policies(business_id, policy_type, is_active);
            ''')
            
            # Inserir dados iniciais
            policies = [
                (1, 'cancellation', 'Política de Cancelamento', 
                 'Cancelamentos devem ser feitos com pelo menos 24 horas de antecedência.',
                 '{"min_hours": 24, "refund": false}'),
                (1, 'rescheduling', 'Política de Reagendamento',
                 'Reagendamentos podem ser feitos até 2 horas antes do horário marcado.',
                 '{"min_hours": 2, "max_reschedules": 2}'),
                (1, 'no_show', 'Política de Falta',
                 'Faltas sem aviso prévio resultam em cobrança de taxa.',
                 '{"fee_percentage": 50, "grace_period": 15}')
            ]
            
            for data in policies:
                await conn.execute('''
                    INSERT INTO business_policies (business_id, policy_type, title, description, rules, is_active)
                    VALUES ($1, $2, $3, $4, $5::json, true)
                ''', *data)
            
            print("✅ Tabela business_policies criada e populada!")
        else:
            print("✅ Tabela business_policies já existe")
        
        # ========================================
        # VERIFICAÇÃO FINAL
        # ========================================
        print("\n🎯 VERIFICAÇÃO FINAL:")
        
        # Contar registros
        count_hours = await conn.fetchval("SELECT COUNT(*) FROM business_hours")
        count_payments = await conn.fetchval("SELECT COUNT(*) FROM payment_methods")
        count_policies = await conn.fetchval("SELECT COUNT(*) FROM business_policies")
        
        print(f"📊 business_hours: {count_hours} registros")
        print(f"📊 payment_methods: {count_payments} registros")
        print(f"📊 business_policies: {count_policies} registros")
        
        await conn.close()
        
        print(f"\n🎉 SUCESSO!")
        print(f"✅ Todas as tabelas foram criadas/verificadas no Railway")
        print(f"✅ Dados iniciais inseridos com sucesso")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(create_missing_tables())
    sys.exit(0 if result else 1)
