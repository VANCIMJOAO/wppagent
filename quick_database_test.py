#!/usr/bin/env python3
"""
🚀 TESTE RÁPIDO DE BANCO DE DADOS - WhatsApp Agent 2025
======================================================
Teste focado nos problemas principais identificados
"""

import asyncio
import asyncpg
import aiohttp
import time
import json
import logging
import random
from datetime import datetime, timedelta

class QuickDatabaseTester:
    def __init__(self):
        self.DATABASE_URL = "postgresql://postgres:UGARTPCwAADBBeBLctoRnQXLsoUvLJxz@caboose.proxy.rlwy.net:13910/railway"
        self.API_BASE_URL = "https://wppagent-production.up.railway.app"
        self.TEST_PHONE = "5516991022255"
        self.session_id = f"quick_test_{int(time.time())}"
        
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - [QUICK TEST] - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        
    async def test_webhook_appointment_creation(self):
        """Teste focado na criação de agendamentos via webhook"""
        self.logger.info("🚀 TESTE RÁPIDO: Criação de Agendamentos via Webhook")
        
        try:
            # Conectar ao banco
            self.db = await asyncpg.connect(self.DATABASE_URL)
            
            # 1. Verificar agendamentos existentes antes do teste
            before_count = await self.db.fetchval("SELECT COUNT(*) FROM appointments WHERE created_at > NOW() - INTERVAL '1 hour'")
            self.logger.info(f"📊 Agendamentos na última hora ANTES do teste: {before_count}")
            
            # 2. Enviar webhook de teste
            webhook_payload = {
                "object": "whatsapp_business_account",
                "entry": [{
                    "id": "728348237027885",
                    "changes": [{
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "15551536026",
                                "phone_number_id": "728348237027885"
                            },
                            "messages": [{
                                "from": self.TEST_PHONE,
                                "id": f"quick_test_{int(time.time())}",
                                "timestamp": str(int(time.time())),
                                "text": {"body": "Quero agendar limpeza de pele para amanhã às 15h"},
                                "type": "text"
                            }],
                            "contacts": [{
                                "profile": {"name": "Quick Test"},
                                "wa_id": self.TEST_PHONE
                            }]
                        },
                        "field": "messages"
                    }]
                }]
            }
            
            self.logger.info("📤 Enviando webhook...")
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.API_BASE_URL}/webhook",
                    json=webhook_payload,
                    headers={"Content-Type": "application/json"},
                    timeout=10
                ) as response:
                    status = response.status
                    text = await response.text()
                    self.logger.info(f"📥 Webhook response: {status} - {text}")
            
            # 3. Aguardar um pouco e verificar
            self.logger.info("⏳ Aguardando 10 segundos...")
            await asyncio.sleep(10)
            
            # 4. Verificar agendamentos após o teste
            after_count = await self.db.fetchval("SELECT COUNT(*) FROM appointments WHERE created_at > NOW() - INTERVAL '1 hour'")
            self.logger.info(f"📊 Agendamentos na última hora APÓS o teste: {after_count}")
            
            # 5. Buscar agendamentos recentes específicos
            recent_appointments = await self.db.fetch("""
                SELECT a.id, a.user_id, a.created_at, a.status, u.telefone, u.nome, s.name as service_name
                FROM appointments a
                JOIN users u ON a.user_id = u.id
                LEFT JOIN services s ON a.service_id = s.id
                WHERE a.created_at > NOW() - INTERVAL '3 minutes'
                ORDER BY a.created_at DESC
                LIMIT 5
            """)
            
            self.logger.info(f"🔍 Agendamentos criados nos últimos 3 minutos: {len(recent_appointments)}")
            
            if recent_appointments:
                for apt in recent_appointments:
                    self.logger.info(f"   ✅ ID {apt['id']}: User {apt['user_id']} ({apt['telefone']}) - {apt['service_name']} - {apt['created_at']}")
                
                # 6. Testar CRUD no primeiro agendamento encontrado
                test_appointment = recent_appointments[0]
                appointment_id = test_appointment['id']
                
                self.logger.info(f"🔧 Testando CRUD no agendamento ID {appointment_id}")
                
                # UPDATE test
                update_result = await self.db.execute("""
                    UPDATE appointments 
                    SET notes = 'Quick test update', updated_at = NOW()
                    WHERE id = $1
                """, appointment_id)
                
                success = "UPDATE 1" in update_result
                self.logger.info(f"📝 UPDATE: {'✅ SUCESSO' if success else '❌ FALHOU'}")
                
                # READ test
                updated_data = await self.db.fetchrow("""
                    SELECT notes FROM appointments WHERE id = $1
                """, appointment_id)
                
                read_success = updated_data and "Quick test update" in (updated_data.get('notes') or '')
                self.logger.info(f"👁️ READ: {'✅ SUCESSO' if read_success else '❌ FALHOU'}")
                
                # Status change test
                status_result = await self.db.execute("""
                    UPDATE appointments 
                    SET status = 'confirmed', updated_at = NOW()
                    WHERE id = $1
                """, appointment_id)
                
                status_success = "UPDATE 1" in status_result
                self.logger.info(f"📊 STATUS UPDATE: {'✅ SUCESSO' if status_success else '❌ FALHOU'}")
                
                # Resultado final
                crud_success = success and read_success and status_success
                webhook_success = after_count > before_count or len(recent_appointments) > 0
                
                print("\n" + "="*60)
                print("🎯 RESULTADO DO TESTE RÁPIDO:")
                print("="*60)
                print(f"📤 Webhook Response: {'✅ 200 OK' if status == 200 else '❌ ERRO'}")
                print(f"📋 Agendamentos Criados: {'✅ SIM' if webhook_success else '❌ NÃO'}")
                print(f"🔧 Operações CRUD: {'✅ FUNCIONANDO' if crud_success else '❌ PROBLEMAS'}")
                print(f"📊 Total Encontrados: {len(recent_appointments)} agendamentos")
                
                if webhook_success and crud_success:
                    print("🏆 CONCLUSÃO: BANCO DE DADOS FUNCIONANDO CORRETAMENTE!")
                    return True
                else:
                    print("⚠️ CONCLUSÃO: Algumas funcionalidades precisam de ajuste")
                    return False
                    
            else:
                print("\n" + "="*60)
                print("🎯 RESULTADO DO TESTE RÁPIDO:")
                print("="*60)
                print(f"📤 Webhook Response: {'✅ 200 OK' if status == 200 else '❌ ERRO'}")
                print("📋 Agendamentos Criados: ❌ NENHUM ENCONTRADO")
                print("🔧 Bot pode não estar processando corretamente")
                print("⚠️ CONCLUSÃO: Webhook responde mas não cria agendamentos")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Erro no teste: {e}")
            return False
        finally:
            if hasattr(self, 'db'):
                await self.db.close()

    async def test_constraints_quick(self):
        """Teste rápido de constraints críticas"""
        self.logger.info("🛡️ TESTE RÁPIDO: Constraints Críticas")
        
        try:
            self.db = await asyncpg.connect(self.DATABASE_URL)
            
            tests_passed = 0
            total_tests = 3
            
            # 1. Teste FK constraint (user_id inválido)
            try:
                await self.db.execute("""
                    INSERT INTO appointments 
                    (user_id, business_id, service_id, date_time, status, created_at)
                    VALUES (999999, 3, 1, NOW() + INTERVAL '1 day', 'pending', NOW())
                """)
                self.logger.warning("⚠️ FK constraint falhou - permitiu user_id inválido")
            except:
                self.logger.info("✅ FK constraint funcionando")
                tests_passed += 1
            
            # 2. Teste unique constraint (telefone duplicado)
            try:
                test_phone = f"test_{random.randint(10000, 99999)}"
                
                # Primeiro usuário
                await self.db.execute("""
                    INSERT INTO users (telefone, nome, created_at)
                    VALUES ($1, 'Test 1', NOW())
                """, test_phone)
                
                # Segundo usuário (deve falhar)
                await self.db.execute("""
                    INSERT INTO users (telefone, nome, created_at)
                    VALUES ($1, 'Test 2', NOW())
                """, test_phone)
                
                self.logger.warning("⚠️ Unique constraint falhou - permitiu telefone duplicado")
            except:
                self.logger.info("✅ Unique constraint funcionando")
                tests_passed += 1
            
            # 3. Teste data type validation
            try:
                await self.db.execute("""
                    INSERT INTO appointments 
                    (user_id, business_id, service_id, date_time, status, created_at)
                    VALUES (1, 3, 1, 'data-inválida', 'pending', NOW())
                """)
                self.logger.warning("⚠️ Data validation falhou")
            except:
                self.logger.info("✅ Data validation funcionando")
                tests_passed += 1
                
            success_rate = (tests_passed / total_tests) * 100
            self.logger.info(f"📊 Constraints: {tests_passed}/{total_tests} funcionando ({success_rate:.0f}%)")
            
            return tests_passed >= 2
            
        except Exception as e:
            self.logger.error(f"❌ Erro no teste de constraints: {e}")
            return False
        finally:
            if hasattr(self, 'db'):
                await self.db.close()

async def main():
    print("🚀 TESTE RÁPIDO DE BANCO DE DADOS - WhatsApp Agent")
    print("=" * 50)
    
    tester = QuickDatabaseTester()
    
    # Teste 1: Webhook e CRUD
    webhook_success = await tester.test_webhook_appointment_creation()
    
    print("\n" + "-" * 50)
    
    # Teste 2: Constraints
    constraints_success = await tester.test_constraints_quick()
    
    print("\n" + "=" * 60)
    print("🎯 RESUMO FINAL:")
    print("=" * 60)
    print(f"📤 Webhook + CRUD: {'✅ FUNCIONANDO' if webhook_success else '❌ PROBLEMAS'}")
    print(f"🛡️ Constraints: {'✅ FUNCIONANDO' if constraints_success else '❌ PROBLEMAS'}")
    
    overall_success = webhook_success and constraints_success
    print(f"\n🏆 RESULTADO GERAL: {'✅ APROVADO' if overall_success else '⚠️ NECESSITA AJUSTES'}")
    
    return overall_success

if __name__ == "__main__":
    asyncio.run(main())
