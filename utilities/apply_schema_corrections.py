#!/usr/bin/env python3
"""
🔧 APLICADOR DE CORREÇÕES SCHEMA APPOINTMENTS
============================================

Aplica as correções necessárias no schema de appointments
no banco Railway de forma segura e controlada.
"""

import asyncio
import sys
from datetime import datetime


async def apply_schema_corrections():
    """Aplica as correções de schema no banco Railway"""
    print("🔧 APLICANDO CORREÇÕES SCHEMA APPOINTMENTS")
    print("=" * 50)
    print(f"⏰ Iniciado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        from app.database import engine
        from sqlalchemy import text
        
        async with engine.begin() as conn:
            print("\n🔍 ETAPA 1: Unificando campos de preço...")
            
            # 1.1 Criar coluna temporária para consolidar preços
            await conn.execute(text("""
                ALTER TABLE appointments ADD COLUMN IF NOT EXISTS price_temp NUMERIC(10,2)
            """))
            print("  ✅ Coluna price_temp criada")
            
            # 1.2 Consolidar dados: price_at_booking tem prioridade
            result = await conn.execute(text("""
                UPDATE appointments 
                SET price_temp = COALESCE(price_at_booking, price, 0.00)
                WHERE price_temp IS NULL
            """))
            print(f"  ✅ {result.rowcount} registros consolidados")
            
            # 1.3 Remover coluna price_at_booking
            await conn.execute(text("ALTER TABLE appointments DROP COLUMN IF EXISTS price_at_booking"))
            print("  ✅ Campo price_at_booking removido")
            
            # 1.4 Renomear price para price_old e price_temp para price
            await conn.execute(text("ALTER TABLE appointments RENAME COLUMN price TO price_old"))
            await conn.execute(text("ALTER TABLE appointments RENAME COLUMN price_temp TO price"))
            print("  ✅ Campo price unificado")
            
            # 1.5 Definir constraints no price
            await conn.execute(text("ALTER TABLE appointments ALTER COLUMN price SET NOT NULL"))
            await conn.execute(text("ALTER TABLE appointments ALTER COLUMN price SET DEFAULT 0.00"))
            print("  ✅ Constraints de price aplicadas")
            
            # 1.6 Remover price_old
            await conn.execute(text("ALTER TABLE appointments DROP COLUMN IF EXISTS price_old"))
            print("  ✅ Campo price_old removido")
            
            print("\n🔍 ETAPA 2: Padronizando campo duração...")
            
            # 2.1 Criar nova coluna duration_minutes
            await conn.execute(text("""
                ALTER TABLE appointments ADD COLUMN IF NOT EXISTS duration_minutes INTEGER DEFAULT 60
            """))
            print("  ✅ Coluna duration_minutes criada")
            
            # 2.2 Migrar dados da coluna duration
            result = await conn.execute(text("""
                UPDATE appointments 
                SET duration_minutes = COALESCE(duration, 60)
                WHERE duration_minutes IS NULL OR duration_minutes = 60
            """))
            print(f"  ✅ {result.rowcount} registros migrados")
            
            # 2.3 Remover coluna antiga duration
            await conn.execute(text("ALTER TABLE appointments DROP COLUMN IF EXISTS duration"))
            print("  ✅ Campo duration removido")
            
            # 2.4 Definir constraints no duration_minutes
            await conn.execute(text("ALTER TABLE appointments ALTER COLUMN duration_minutes SET NOT NULL"))
            print("  ✅ Constraints de duration_minutes aplicadas")
            
            print("\n🔍 ETAPA 3: Criando trigger para end_time...")
            
            # 3.1 Criar função para calcular end_time
            await conn.execute(text("""
                CREATE OR REPLACE FUNCTION calculate_appointment_end_time()
                RETURNS TRIGGER AS $$
                BEGIN
                    -- Calcular end_time automaticamente baseado em date_time + duration_minutes
                    IF NEW.date_time IS NOT NULL AND NEW.duration_minutes IS NOT NULL THEN
                        NEW.end_time = NEW.date_time + (NEW.duration_minutes || ' minutes')::INTERVAL;
                    END IF;
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;
            """))
            print("  ✅ Função calculate_appointment_end_time criada")
            
            # 3.2 Criar trigger
            await conn.execute(text("DROP TRIGGER IF EXISTS appointment_end_time_trigger ON appointments"))
            await conn.execute(text("""
                CREATE TRIGGER appointment_end_time_trigger
                    BEFORE INSERT OR UPDATE ON appointments
                    FOR EACH ROW
                    EXECUTE FUNCTION calculate_appointment_end_time()
            """))
            print("  ✅ Trigger appointment_end_time_trigger criado")
            
            # 3.3 Recalcular todos os end_time existentes
            result = await conn.execute(text("""
                UPDATE appointments 
                SET end_time = date_time + (duration_minutes || ' minutes')::INTERVAL
                WHERE date_time IS NOT NULL AND duration_minutes IS NOT NULL
            """))
            print(f"  ✅ {result.rowcount} end_time recalculados")
            
            print("\n🔍 ETAPA 4: Otimizações adicionais...")
            
            # 4.1 Criar índices para performance
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_appointments_date_time ON appointments(date_time)
            """))
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_appointments_status ON appointments(status)  
            """))
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_appointments_user_date ON appointments(user_id, date_time)
            """))
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_appointments_price ON appointments(price)
            """))
            print("  ✅ Índices de performance criados")
            
            # 4.2 Verificar resultado final
            result = await conn.execute(text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'appointments' 
                AND column_name IN ('price', 'duration_minutes', 'price_at_booking', 'duration')
                ORDER BY column_name
            """))
            
            final_columns = {row[0]: {'type': row[1], 'nullable': row[2], 'default': row[3]} 
                           for row in result.fetchall()}
            
            print(f"\n📊 RESULTADO FINAL:")
            print(f"  ✅ price: {'SIM' if 'price' in final_columns else 'NÃO'}")
            print(f"  ✅ duration_minutes: {'SIM' if 'duration_minutes' in final_columns else 'NÃO'}")
            print(f"  ❌ price_at_booking: {'AINDA EXISTE' if 'price_at_booking' in final_columns else 'REMOVIDO'}")
            print(f"  ❌ duration: {'AINDA EXISTE' if 'duration' in final_columns else 'REMOVIDO'}")
            
            # 4.3 Verificar dados finais
            result = await conn.execute(text("SELECT COUNT(*) FROM appointments"))
            total_final = result.scalar()
            
            result = await conn.execute(text("""
                SELECT COUNT(*) FROM appointments 
                WHERE price IS NOT NULL AND duration_minutes IS NOT NULL AND end_time IS NOT NULL
            """))
            complete_records = result.scalar()
            
            print(f"\n📈 DADOS FINAIS:")
            print(f"  📊 Total appointments: {total_final}")
            print(f"  ✅ Registros completos: {complete_records}")
            
            if complete_records == total_final:
                print("  🎉 TODOS OS REGISTROS MIGRADOS COM SUCESSO!")
                return True
            else:
                print(f"  ⚠️ {total_final - complete_records} registros incompletos")
                return False
            
    except Exception as e:
        print(f"\n❌ Erro durante a aplicação: {e}")
        return False


async def main():
    """Executa aplicação das correções"""
    try:
        # Definir DATABASE_URL temporariamente se não estiver definida
        import os
        if not os.getenv('DATABASE_URL'):
            os.environ['DATABASE_URL'] = "postgresql://postgres:UGARTPCwAADBBeBLctoRnQXLsoUvLJxz@caboose.proxy.rlwy.net:13910/railway"
            print("🔗 DATABASE_URL configurada temporariamente")
        
        success = await apply_schema_corrections()
        
        if success:
            print("\n🎉 CORREÇÕES APLICADAS COM SUCESSO!")
            print("✅ Schema appointments padronizado")
            print("✅ Campos duplicados eliminados") 
            print("✅ Dados preservados")
            print("✅ Triggers e índices criados")
            print("\n📋 O que foi corrigido:")
            print("   • price_at_booking → price (unificado)")
            print("   • duration → duration_minutes (padronizado)")  
            print("   • end_time calculado automaticamente")
            print("   • Índices de performance adicionados")
        else:
            print("\n⚠️ CORREÇÕES INCOMPLETAS")
            print("   Verifique os logs acima")
        
        return success
        
    except Exception as e:
        print(f"\n💥 Erro crítico: {e}")
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Operação interrompida pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Erro crítico: {e}")
        sys.exit(1)
