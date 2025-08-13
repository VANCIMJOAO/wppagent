#!/usr/bin/env python3
"""
Script Simples para Criar Tabelas - Via psycopg2
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor

def create_tables():
    print("🔧 CRIANDO TABELAS DE NEGÓCIO (via psycopg2)")
    print("=" * 50)
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL não encontrada")
        return
    
    try:
        # Conectar com psycopg2
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # SQL das tabelas
        sqls = [
            # 1. business_hours
            """
            CREATE TABLE IF NOT EXISTS business_hours (
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
            """,
            "CREATE INDEX IF NOT EXISTS idx_business_hours_business_day ON business_hours(business_id, day_of_week);",
            
            # 2. payment_methods
            """
            CREATE TABLE IF NOT EXISTS payment_methods (
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
            """,
            "CREATE INDEX IF NOT EXISTS idx_payment_methods_business ON payment_methods(business_id, is_active);",
            
            # 3. business_policies
            """
            CREATE TABLE IF NOT EXISTS business_policies (
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
            """,
            "CREATE INDEX IF NOT EXISTS idx_business_policies_business_type ON business_policies(business_id, policy_type, is_active);"
        ]
        
        # Executar SQLs
        for i, sql in enumerate(sqls, 1):
            try:
                cursor.execute(sql)
                print(f"✅ SQL {i} executado com sucesso")
            except Exception as e:
                print(f"⚠️  SQL {i} falhou: {e}")
        
        # Inserir dados iniciais se não existirem
        print("\n📋 Inserindo dados iniciais...")
        
        # Verificar se já existem dados
        cursor.execute("SELECT COUNT(*) FROM business_hours WHERE business_id = 1")
        bh_count = cursor.fetchone()[0]
        
        if bh_count == 0:
            # Inserir horários de funcionamento
            business_hours_data = [
                (1, 0, False, None, None, 'Fechado aos domingos'),
                (1, 1, True, '09:00:00', '18:00:00', 'Segunda-feira'),
                (1, 2, True, '09:00:00', '18:00:00', 'Terça-feira'),
                (1, 3, True, '09:00:00', '18:00:00', 'Quarta-feira'),
                (1, 4, True, '09:00:00', '18:00:00', 'Quinta-feira'),
                (1, 5, True, '09:00:00', '18:00:00', 'Sexta-feira'),
                (1, 6, False, None, None, 'Fechado aos sábados')
            ]
            
            cursor.executemany("""
                INSERT INTO business_hours (business_id, day_of_week, is_open, open_time, close_time, notes)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, business_hours_data)
            print("✅ Horários de funcionamento inseridos!")
        
        # Verificar formas de pagamento
        cursor.execute("SELECT COUNT(*) FROM payment_methods WHERE business_id = 1")
        pm_count = cursor.fetchone()[0]
        
        if pm_count == 0:
            payment_methods_data = [
                (1, 'Dinheiro', 'Pagamento em espécie', 1, True),
                (1, 'PIX', 'Transferência instantânea', 2, True),
                (1, 'Cartão de Débito', 'Cartão de débito', 3, True),
                (1, 'Cartão de Crédito', 'Cartão de crédito', 4, True)
            ]
            
            cursor.executemany("""
                INSERT INTO payment_methods (business_id, name, description, display_order, is_active)
                VALUES (%s, %s, %s, %s, %s)
            """, payment_methods_data)
            print("✅ Formas de pagamento inseridas!")
        
        # Verificar políticas
        cursor.execute("SELECT COUNT(*) FROM business_policies WHERE business_id = 1")
        bp_count = cursor.fetchone()[0]
        
        if bp_count == 0:
            import json
            policies_data = [
                (1, 'cancellation', 'Política de Cancelamento', 
                 'Cancelamentos devem ser feitos com pelo menos 24 horas de antecedência.',
                 json.dumps({"min_hours": 24, "refund": False}), True),
                (1, 'rescheduling', 'Política de Reagendamento',
                 'Reagendamentos podem ser feitos até 2 horas antes do horário marcado.',
                 json.dumps({"min_hours": 2, "max_reschedules": 2}), True),
                (1, 'no_show', 'Política de Falta',
                 'Faltas sem aviso prévio resultam em cobrança de taxa.',
                 json.dumps({"fee_percentage": 50, "grace_period": 15}), True)
            ]
            
            cursor.executemany("""
                INSERT INTO business_policies (business_id, policy_type, title, description, rules, is_active)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, policies_data)
            print("✅ Políticas do negócio inseridas!")
        
        # Commit
        conn.commit()
        
        print(f"\n🎉 TABELAS CRIADAS COM SUCESSO!")
        print(f"✅ business_hours: {7} registros")
        print(f"✅ payment_methods: {4} registros") 
        print(f"✅ business_policies: {3} registros")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    create_tables()
