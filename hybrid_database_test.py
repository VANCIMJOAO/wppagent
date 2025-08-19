#!/usr/bin/env python3
"""
🎯 TESTE HÍBRIDO DE BANCO DE DADOS - WhatsApp Agent 2025
======================================================
Combina a eficiência do teste rápido com a completude do teste full
"""

import asyncio
import asyncpg
import aiohttp
import time
import json
import logging
import random
from datetime import datetime, timedelta

class HybridDatabaseTester:
    def __init__(self):
        self.DATABASE_URL = "postgresql://postgres:UGARTPCwAADBBeBLctoRnQXLsoUvLJxz@caboose.proxy.rlwy.net:13910/railway"
        self.API_BASE_URL = "https://wppagent-production.up.railway.app"
        self.TEST_PHONE = "5516991022255"
        self.session_id = f"hybrid_test_{int(time.time())}"
        
        self.test_results = []
        self.test_appointment_ids = []
        self.test_user_ids = []
        
        logging.basicConfig(
            level=logging.INFO, 
            format='%(asctime)s - [HYBRID TEST] - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(f'hybrid_test_{self.session_id}.log')
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    async def connect_database(self):
        """Conecta ao banco de dados"""
        try:
            self.db = await asyncpg.connect(self.DATABASE_URL)
            self.logger.info("✅ Conexão com banco estabelecida")
            return True
        except Exception as e:
            self.logger.error(f"❌ Erro ao conectar no banco: {e}")
            return False
    
    async def test_webhook_and_crud(self):
        """Teste 1: Webhook + CRUD (baseado no teste rápido que funciona)"""
        self.logger.info("🚀 TESTE 1: Webhook + CRUD de Agendamentos")
        
        errors = []
        warnings = []
        records_affected = 0
        test_data = {}
        start_time = time.time()
        
        try:
            # 1. Verificar agendamentos antes
            before_count = await self.db.fetchval("SELECT COUNT(*) FROM appointments WHERE created_at > NOW() - INTERVAL '30 minutes'")
            
            # 2. Enviar webhook
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
                                "id": f"hybrid_test_{int(time.time())}",
                                "timestamp": str(int(time.time())),
                                "text": {"body": "Quero agendar limpeza de pele para amanhã às 16h"},
                                "type": "text"
                            }],
                            "contacts": [{
                                "profile": {"name": "Hybrid Test"},
                                "wa_id": self.TEST_PHONE
                            }]
                        },
                        "field": "messages"
                    }]
                }]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.API_BASE_URL}/webhook",
                    json=webhook_payload,
                    headers={"Content-Type": "application/json"},
                    timeout=10
                ) as response:
                    webhook_status = response.status
                    webhook_text = await response.text()
                    
                    if webhook_status == 200:
                        test_data["webhook_success"] = True
                        records_affected += 1
                        self.logger.info("✅ Webhook processado com sucesso")
                    else:
                        errors.append(f"Webhook falhou: {webhook_status}")
                        test_data["webhook_success"] = False
            
            # 3. Aguardar e verificar
            await asyncio.sleep(8)
            
            # 4. Buscar agendamentos criados
            recent_appointments = await self.db.fetch("""
                SELECT a.id, a.user_id, a.created_at, a.status, u.telefone, u.nome, s.name as service_name
                FROM appointments a
                JOIN users u ON a.user_id = u.id
                LEFT JOIN services s ON a.service_id = s.id
                WHERE a.created_at > $1
                ORDER BY a.created_at DESC
                LIMIT 3
            """, datetime.now() - timedelta(minutes=3))
            
            test_data["appointments_found"] = len(recent_appointments)
            
            if recent_appointments:
                # Sucesso na criação - testar CRUD
                appointment_id = recent_appointments[0]['id']
                self.test_appointment_ids.append(appointment_id)
                records_affected += 1
                
                self.logger.info(f"✅ Agendamento encontrado: ID {appointment_id}")
                
                # UPDATE
                update_result = await self.db.execute("""
                    UPDATE appointments 
                    SET notes = 'Hybrid test update', updated_at = NOW()
                    WHERE id = $1
                """, appointment_id)
                
                if "UPDATE 1" in update_result:
                    records_affected += 1
                    test_data["update_success"] = True
                    
                    # READ
                    updated_data = await self.db.fetchrow("""
                        SELECT notes FROM appointments WHERE id = $1
                    """, appointment_id)
                    
                    if updated_data and "Hybrid test update" in (updated_data.get('notes') or ''):
                        test_data["read_success"] = True
                        records_affected += 1
                    else:
                        errors.append("Falha na verificação de UPDATE")
                    
                    # STATUS UPDATE
                    status_result = await self.db.execute("""
                        UPDATE appointments 
                        SET status = 'confirmed', updated_at = NOW()
                        WHERE id = $1
                    """, appointment_id)
                    
                    if "UPDATE 1" in status_result:
                        test_data["status_update_success"] = True
                        records_affected += 1
                    else:
                        errors.append("Falha no update de status")
                        
                    # CANCEL (soft delete)
                    cancel_result = await self.db.execute("""
                        UPDATE appointments 
                        SET status = 'cancelled', 
                            cancelled_at = NOW(),
                            cancellation_reason = 'Hybrid test cancel'
                        WHERE id = $1
                    """, appointment_id)
                    
                    if "UPDATE 1" in cancel_result:
                        test_data["cancel_success"] = True
                        records_affected += 1
                    else:
                        errors.append("Falha no cancelamento")
                else:
                    errors.append("Falha no UPDATE inicial")
            else:
                errors.append("Nenhum agendamento foi criado pelo bot")
                test_data["webhook_creates_appointments"] = False
                
        except Exception as e:
            errors.append(f"Erro no teste webhook: {str(e)}")
            self.logger.error(f"❌ Erro: {e}")
        
        execution_time = time.time() - start_time
        success = len(errors) == 0 and test_data.get("appointments_found", 0) > 0
        data_validation = all([
            test_data.get("update_success", False),
            test_data.get("read_success", False),
            test_data.get("status_update_success", False)
        ])
        
        result = {
            "test_name": "Webhook + CRUD Operations",
            "success": success,
            "errors": errors,
            "warnings": warnings,
            "execution_time": execution_time,
            "records_affected": records_affected,
            "data_validation_passed": data_validation,
            "is_critical": True,
            "test_data": test_data
        }
        
        self.test_results.append(result)
        return result
    
    async def test_constraints_comprehensive(self):
        """Teste 2: Constraints e Integridade"""
        self.logger.info("🛡️ TESTE 2: Constraints e Integridade de Dados")
        
        errors = []
        warnings = []
        records_affected = 0
        test_data = {}
        start_time = time.time()
        
        try:
            validations_passed = 0
            total_validations = 6
            
            # 1. FK constraint - user_id inválido
            try:
                await self.db.execute("""
                    INSERT INTO appointments 
                    (user_id, business_id, service_id, date_time, status, created_at)
                    VALUES (999999, 3, 1, NOW() + INTERVAL '1 day', 'pending', NOW())
                """)
                errors.append("FK constraint falhou - user_id inválido aceito")
            except:
                test_data["fk_user_constraint"] = "working"
                validations_passed += 1
                self.logger.info("✅ FK constraint user_id funcionando")
            
            # 2. FK constraint - service_id inválido
            try:
                temp_user = await self.create_test_user()
                await self.db.execute("""
                    INSERT INTO appointments 
                    (user_id, business_id, service_id, date_time, status, created_at)
                    VALUES ($1, 3, 999999, NOW() + INTERVAL '1 day', 'pending', NOW())
                """, temp_user)
                errors.append("FK constraint falhou - service_id inválido aceito")
            except:
                test_data["fk_service_constraint"] = "working"
                validations_passed += 1
                self.logger.info("✅ FK constraint service_id funcionando")
            
            # 3. Unique constraint - telefone
            try:
                test_phone = f"test_{random.randint(10000, 99999)}"
                
                user1 = await self.db.fetchval("""
                    INSERT INTO users (telefone, nome, created_at)
                    VALUES ($1, 'Test 1', NOW())
                    RETURNING id
                """, test_phone)
                
                if user1:
                    self.test_user_ids.append(user1)
                    records_affected += 1
                
                user2 = await self.db.fetchval("""
                    INSERT INTO users (telefone, nome, created_at)
                    VALUES ($1, 'Test 2', NOW())
                    RETURNING id
                """, test_phone)
                
                if user2:
                    errors.append("Unique constraint falhou - telefone duplicado aceito")
                    self.test_user_ids.append(user2)
                    
            except:
                test_data["unique_phone_constraint"] = "working"
                validations_passed += 1
                self.logger.info("✅ Unique constraint telefone funcionando")
            
            # 4. Data type validation
            try:
                await self.db.execute("""
                    INSERT INTO appointments 
                    (user_id, business_id, service_id, date_time, status, created_at)
                    VALUES (1, 3, 1, 'data-inválida', 'pending', NOW())
                """)
                errors.append("Data validation falhou - data inválida aceita")
            except:
                test_data["date_format_validation"] = "working"
                validations_passed += 1
                self.logger.info("✅ Data validation funcionando")
            
            # 5. Cascade protection
            if self.test_user_ids:
                user_id = self.test_user_ids[0]
                
                # Criar agendamento para o usuário
                appointment_id = await self.db.fetchval("""
                    INSERT INTO appointments 
                    (user_id, business_id, service_id, date_time, status, created_at)
                    VALUES ($1, 3, 1, NOW() + INTERVAL '1 day', 'pending', NOW())
                    RETURNING id
                """, user_id)
                
                if appointment_id:
                    self.test_appointment_ids.append(appointment_id)
                    records_affected += 1
                    
                    # Tentar deletar usuário com dependências
                    try:
                        await self.db.execute("DELETE FROM users WHERE id = $1", user_id)
                        errors.append("Cascade protection falhou - usuário com dependências foi deletado")
                    except:
                        test_data["cascade_protection"] = "working"
                        validations_passed += 1
                        self.logger.info("✅ Cascade protection funcionando")
            
            # 6. Transaction rollback
            try:
                async with self.db.transaction():
                    temp_user = await self.db.fetchval("""
                        INSERT INTO users (telefone, nome, created_at)
                        VALUES ($1, 'Temp User', NOW())
                        RETURNING id
                    """, f"temp_{int(time.time())}")
                    
                    # Forçar erro
                    await self.db.execute("""
                        INSERT INTO appointments 
                        (user_id, business_id, service_id, date_time, status, created_at)
                        VALUES ($1, 3, 999999, NOW() + INTERVAL '1 day', 'pending', NOW())
                    """, temp_user)
                    
            except:
                # Verificar se rollback funcionou
                user_exists = await self.db.fetchval("""
                    SELECT COUNT(*) FROM users WHERE telefone = $1
                """, f"temp_{int(time.time())}")
                
                if user_exists == 0:
                    test_data["transaction_rollback"] = "working"
                    validations_passed += 1
                    self.logger.info("✅ Transaction rollback funcionando")
                else:
                    errors.append("Transaction rollback falhou")
            
            test_data["validations_passed"] = validations_passed
            test_data["total_validations"] = total_validations
            
        except Exception as e:
            errors.append(f"Erro no teste de constraints: {str(e)}")
            self.logger.error(f"❌ Erro: {e}")
        
        execution_time = time.time() - start_time
        success = len(errors) == 0 and validations_passed >= 4
        data_validation = validations_passed >= 4
        
        result = {
            "test_name": "Data Constraints & Integrity",
            "success": success,
            "errors": errors,
            "warnings": warnings,
            "execution_time": execution_time,
            "records_affected": records_affected,
            "data_validation_passed": data_validation,
            "is_critical": True,
            "test_data": test_data
        }
        
        self.test_results.append(result)
        return result
    
    async def test_customer_management_quick(self):
        """Teste 3: Gerenciamento de Clientes (versão otimizada)"""
        self.logger.info("👥 TESTE 3: Gerenciamento de Clientes")
        
        errors = []
        warnings = []
        records_affected = 0
        test_data = {}
        start_time = time.time()
        
        try:
            # Criar usuário via webhook
            timestamp = str(int(time.time()))[-6:]
            phone = f"551199{timestamp}999"[:20]
            
            # Simular primeira interação
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
                                "from": phone,
                                "id": f"customer_test_{int(time.time())}",
                                "timestamp": str(int(time.time())),
                                "text": {"body": "Olá! Meu nome é Maria Silva"},
                                "type": "text"
                            }],
                            "contacts": [{
                                "profile": {"name": "Maria Silva"},
                                "wa_id": phone
                            }]
                        },
                        "field": "messages"
                    }]
                }]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.API_BASE_URL}/webhook",
                    json=webhook_payload,
                    timeout=10
                ) as response:
                    if response.status == 200:
                        records_affected += 1
                        test_data["user_creation_webhook"] = True
            
            await asyncio.sleep(3)
            
            # Verificar se usuário foi criado
            user_record = await self.db.fetchrow("""
                SELECT * FROM users 
                WHERE telefone = $1 OR wa_id = $1
                ORDER BY created_at DESC
                LIMIT 1
            """, phone)
            
            if user_record:
                user_id = user_record['id']
                self.test_user_ids.append(user_id)
                test_data["user_created"] = True
                records_affected += 1
                self.logger.info(f"✅ Usuário criado via webhook: ID {user_id}")
                
                # Testar update manual
                update_result = await self.db.execute("""
                    UPDATE users 
                    SET nome = 'Maria Silva Santos', updated_at = NOW()
                    WHERE id = $1
                """, user_id)
                
                if "UPDATE 1" in update_result:
                    test_data["user_update"] = True
                    records_affected += 1
                
                # Verificar conversas
                conversations = await self.db.fetch("""
                    SELECT * FROM conversations 
                    WHERE user_id = $1
                    ORDER BY created_at DESC
                """, user_id)
                
                test_data["conversations_count"] = len(conversations)
                if conversations:
                    records_affected += len(conversations)
                
            else:
                errors.append("Usuário não foi criado via webhook")
                test_data["user_created"] = False
            
        except Exception as e:
            errors.append(f"Erro no teste de clientes: {str(e)}")
            self.logger.error(f"❌ Erro: {e}")
        
        execution_time = time.time() - start_time
        success = len(errors) == 0 and test_data.get("user_created", False)
        data_validation = test_data.get("user_created", False) and records_affected >= 2
        
        result = {
            "test_name": "Customer Management",
            "success": success,
            "errors": errors,
            "warnings": warnings,
            "execution_time": execution_time,
            "records_affected": records_affected,
            "data_validation_passed": data_validation,
            "is_critical": True,
            "test_data": test_data
        }
        
        self.test_results.append(result)
        return result
    
    async def create_test_user(self):
        """Cria um usuário de teste"""
        timestamp = str(int(time.time()))[-6:]
        random_suffix = str(random.randint(100, 999))
        phone = f"5516991{timestamp}{random_suffix}"[:20]
        
        user_id = await self.db.fetchval("""
            INSERT INTO users (wa_id, telefone, nome, created_at, updated_at)
            VALUES ($1, $2, $3, NOW(), NOW())
            RETURNING id
        """, phone, phone, f"Test{timestamp}")
        
        if user_id:
            self.test_user_ids.append(user_id)
        
        return user_id
    
    async def cleanup_test_data(self):
        """Limpeza robusta de dados"""
        self.logger.info("🧹 Limpando dados de teste...")
        
        try:
            # Limpar agendamentos primeiro
            if self.test_appointment_ids:
                await self.db.execute("""
                    DELETE FROM appointments WHERE id = ANY($1)
                """, self.test_appointment_ids)
                self.logger.info(f"🗑️ {len(self.test_appointment_ids)} agendamentos removidos")
            
            # Limpar usuários e suas dependências
            if self.test_user_ids:
                for user_id in self.test_user_ids:
                    try:
                        # Limpar dependências
                        await self.db.execute("DELETE FROM appointments WHERE user_id = $1", user_id)
                        await self.db.execute("DELETE FROM messages WHERE user_id = $1", user_id)
                        await self.db.execute("DELETE FROM conversations WHERE user_id = $1", user_id)
                        # Limpar usuário
                        await self.db.execute("DELETE FROM users WHERE id = $1", user_id)
                    except Exception as e:
                        self.logger.warning(f"⚠️ Erro ao limpar usuário {user_id}: {e}")
                
                self.logger.info(f"👤 {len(self.test_user_ids)} usuários processados para limpeza")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Erro na limpeza: {e}")
    
    async def generate_final_report(self):
        """Gerar relatório final"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        critical_tests = sum(1 for result in self.test_results if result["is_critical"])
        critical_passed = sum(1 for result in self.test_results if result["is_critical"] and result["success"])
        
        total_records = sum(result["records_affected"] for result in self.test_results)
        total_validations = sum(1 for result in self.test_results if result["data_validation_passed"])
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        critical_rate = (critical_passed / critical_tests * 100) if critical_tests > 0 else 0
        
        overall_success = success_rate >= 80 and critical_rate == 100
        
        print("\n" + "="*70)
        print("🎯 RELATÓRIO HÍBRIDO - BANCO DE DADOS WhatsApp Agent")
        print("="*70)
        print(f"🆔 Sessão: {self.session_id}")
        print(f"📅 Executado: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}")
        
        print(f"\n📊 RESULTADOS:")
        print(f"  📈 Total de testes: {total_tests}")
        print(f"  ✅ Testes aprovados: {passed_tests}")
        print(f"  🎯 Taxa de sucesso: {success_rate:.1f}%")
        print(f"  🚨 Testes críticos: {critical_tests}")
        print(f"  ✅ Críticos aprovados: {critical_passed}")
        print(f"  🎯 Taxa crítica: {critical_rate:.1f}%")
        print(f"  📝 Registros processados: {total_records}")
        print(f"  ✔️ Validações aprovadas: {total_validations}/{total_tests}")
        
        print(f"\n📋 DETALHES:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            critical = "🚨" if result["is_critical"] else "📝"
            validation = "✔️" if result["data_validation_passed"] else "❌"
            
            print(f"  {status} {critical} {result['test_name']}")
            print(f"      ⏱️ Tempo: {result['execution_time']:.2f}s")
            print(f"      📊 Registros: {result['records_affected']}")
            print(f"      {validation} Validação: {'PASSOU' if result['data_validation_passed'] else 'FALHOU'}")
            
            for error in result["errors"]:
                print(f"      ❌ {error}")
                
            for warning in result["warnings"]:
                print(f"      ⚠️ {warning}")
        
        print(f"\n🏆 CONCLUSÃO:")
        if overall_success:
            print("   ✅ BANCO DE DADOS TOTALMENTE APROVADO!")
            print("   🚀 Sistema pronto para produção")
            conclusion = "DATABASE FULLY APPROVED"
        elif critical_rate == 100:
            print("   ⚠️ BANCO DE DADOS FUNCIONANDO")
            print("   🔧 Pequenos ajustes recomendados")
            conclusion = "DATABASE FUNCTIONAL"
        else:
            print("   ❌ BANCO DE DADOS COM PROBLEMAS")
            print("   🚨 Correções necessárias")
            conclusion = "DATABASE NEEDS FIXES"
        
        print("="*70)
        
        # Salvar relatório
        report = {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "overall_success": overall_success,
            "success_rate": success_rate,
            "critical_success_rate": critical_rate,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "critical_tests": critical_tests,
            "critical_passed": critical_passed,
            "total_records_affected": total_records,
            "validations_passed": total_validations,
            "conclusion": conclusion,
            "test_results": self.test_results
        }
        
        filename = f"hybrid_test_report_{self.session_id}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n📄 Relatório salvo: {filename}")
        return overall_success
    
    async def run_all_tests(self):
        """Executa todos os testes"""
        self.logger.info("🚀 INICIANDO TESTE HÍBRIDO DE BANCO DE DADOS")
        
        if not await self.connect_database():
            print("❌ Falha na conexão com banco de dados")
            return False
        
        try:
            # Executar testes
            await self.test_webhook_and_crud()
            await self.test_constraints_comprehensive()
            await self.test_customer_management_quick()
            
            # Gerar relatório
            return await self.generate_final_report()
            
        except Exception as e:
            self.logger.error(f"❌ Erro durante testes: {e}")
            return False
        finally:
            await self.cleanup_test_data()
            if hasattr(self, 'db'):
                await self.db.close()

async def main():
    print("🎯 TESTE HÍBRIDO DE BANCO DE DADOS - WhatsApp Agent")
    print("=" * 50)
    print("📋 Este teste combina eficiência e completude:")
    print("   🚀 Webhook + CRUD (baseado no teste rápido)")
    print("   🛡️ Constraints e Integridade")
    print("   👥 Gerenciamento de Clientes")
    print("=" * 50)
    
    tester = HybridDatabaseTester()
    success = await tester.run_all_tests()
    
    if success:
        print("\n🎉 SUCESSO! Sistema aprovado!")
        return True
    else:
        print("\n⚠️ Sistema necessita ajustes")
        return False

if __name__ == "__main__":
    asyncio.run(main())
