#!/usr/bin/env python3
"""
Script para Criar Tabelas de Negócio Faltantes
WhatsApp Agent - Execução direta das migrações
"""

import asyncio
import sqlalchemy as sa
from app.database import engine

async def create_missing_business_tables():
    """Criar tabelas de negócio que estão faltando"""
    print("🔧 CRIANDO TABELAS DE NEGÓCIO FALTANTES")
    print("=" * 50)
    
    try:
        async with engine.begin() as conn:
            # Verificar quais tabelas existem
            result = await conn.execute(
                sa.text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
            )
            existing_tables = [row[0] for row in result.fetchall()]
            print(f"📋 Tabelas existentes: {len(existing_tables)}")
            
            # Tabelas que precisam ser criadas
            required_tables = {
                'business_hours': '''
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
                ''',
                'payment_methods': '''
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
                ''',
                'business_policies': '''
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
                '''
            }
            
            # Criar tabelas faltantes
            for table_name, create_sql in required_tables.items():
                if table_name not in existing_tables:
                    print(f"🔧 Criando tabela: {table_name}")
                    try:
                        await conn.execute(sa.text(create_sql))
                        print(f"✅ Tabela {table_name} criada com sucesso!")
                    except Exception as e:
                        print(f"❌ Erro ao criar {table_name}: {e}")
                else:
                    print(f"✅ Tabela {table_name} já existe")
            
            # Inserir dados iniciais
            print(f"\n📋 Inserindo dados iniciais...")
            
            # Dados para business_hours (segunda a sexta 9h-18h)
            business_hours_data = []
            for day in range(7):  # 0=domingo, 1=segunda, ..., 6=sábado
                if day in [1, 2, 3, 4, 5]:  # Segunda a sexta
                    business_hours_data.append({
                        'business_id': 1,
                        'day_of_week': day,
                        'is_open': True,
                        'open_time': '09:00:00',
                        'close_time': '18:00:00',
                        'notes': 'Horário comercial padrão'
                    })
                else:  # Fins de semana
                    business_hours_data.append({
                        'business_id': 1,
                        'day_of_week': day,
                        'is_open': False,
                        'notes': 'Fechado aos fins de semana'
                    })
            
            # Inserir horários de funcionamento
            try:
                if 'business_hours' not in existing_tables:
                    for bh in business_hours_data:
                        await conn.execute(sa.text('''
                            INSERT INTO business_hours (business_id, day_of_week, is_open, open_time, close_time, notes)
                            VALUES (:business_id, :day_of_week, :is_open, :open_time, :close_time, :notes)
                        '''), bh)
                    print("✅ Horários de funcionamento inseridos!")
            except Exception as e:
                print(f"⚠️  Erro ao inserir horários: {e}")
            
            # Inserir formas de pagamento
            try:
                if 'payment_methods' not in existing_tables:
                    payment_methods = [
                        {'business_id': 1, 'name': 'Dinheiro', 'description': 'Pagamento em espécie', 'display_order': 1},
                        {'business_id': 1, 'name': 'PIX', 'description': 'Transferência instantânea', 'display_order': 2},
                        {'business_id': 1, 'name': 'Cartão de Débito', 'description': 'Cartão de débito', 'display_order': 3},
                        {'business_id': 1, 'name': 'Cartão de Crédito', 'description': 'Cartão de crédito', 'display_order': 4}
                    ]
                    
                    for pm in payment_methods:
                        await conn.execute(sa.text('''
                            INSERT INTO payment_methods (business_id, name, description, display_order, is_active)
                            VALUES (:business_id, :name, :description, :display_order, true)
                        '''), pm)
                    print("✅ Formas de pagamento inseridas!")
            except Exception as e:
                print(f"⚠️  Erro ao inserir formas de pagamento: {e}")
                
            # Inserir políticas do negócio
            try:
                if 'business_policies' not in existing_tables:
                    policies = [
                        {
                            'business_id': 1,
                            'policy_type': 'cancellation',
                            'title': 'Política de Cancelamento',
                            'description': 'Cancelamentos devem ser feitos com pelo menos 24 horas de antecedência.',
                            'rules': '{"min_hours": 24, "refund": false}'
                        },
                        {
                            'business_id': 1,
                            'policy_type': 'rescheduling',
                            'title': 'Política de Reagendamento',
                            'description': 'Reagendamentos podem ser feitos até 2 horas antes do horário marcado.',
                            'rules': '{"min_hours": 2, "max_reschedules": 2}'
                        }
                    ]
                    
                    for policy in policies:
                        await conn.execute(sa.text('''
                            INSERT INTO business_policies (business_id, policy_type, title, description, rules, is_active)
                            VALUES (:business_id, :policy_type, :title, :description, :rules::json, true)
                        '''), policy)
                    print("✅ Políticas do negócio inseridas!")
            except Exception as e:
                print(f"⚠️  Erro ao inserir políticas: {e}")
            
            print(f"\n🎉 MIGRAÇÃO COMPLETA!")
            print(f"✅ Todas as tabelas de negócio foram criadas/verificadas")
            print(f"✅ Dados iniciais inseridos com sucesso")
            
    except Exception as e:
        print(f"❌ Erro geral na migração: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(create_missing_business_tables())
