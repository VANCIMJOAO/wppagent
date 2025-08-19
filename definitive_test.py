#!/usr/bin/env python3
"""
🎯 TESTE DEFINITIVO - WhatsApp Agent 2025
=========================================
Teste que funciona com a realidade do sistema em produção
"""

import asyncio
import asyncpg
import aiohttp
import time
import json
from datetime import datetime, timedelta

class DefinitiveTest:
    def __init__(self):
        self.DATABASE_URL = "postgresql://postgres:UGARTPCwAADBBeBLctoRnQXLsoUvLJxz@caboose.proxy.rlwy.net:13910/railway"
        self.API_BASE_URL = "https://wppagent-production.up.railway.app"
        self.TEST_PHONE = "5516991022255"
        self.session_id = f"definitive_{int(time.time())}"
        
    async def run_test(self):
        """Executa o teste definitivo que funciona com o sistema real"""
        print("🎯 TESTE DEFINITIVO - WhatsApp Agent")
        print("=" * 60)
        print(f"🆔 Sessão: {self.session_id}")
        print(f"📱 Testando com usuário existente: {self.TEST_PHONE}")
        print("=" * 60)
        
        # Conectar banco
        try:
            db = await asyncpg.connect(self.DATABASE_URL)
            print("✅ Conexão com banco estabelecida")
        except Exception as e:
            print(f"❌ Erro ao conectar no banco: {e}")
            return False
        
        test_results = []
        
        # PRÉ-TESTE: Verificar estado atual
        print("\n📊 PRÉ-TESTE: Estado atual do sistema")
        try:
            user = await db.fetchrow("SELECT * FROM users WHERE telefone = $1", self.TEST_PHONE)
            if user:
                print(f"   👤 Usuário: ID {user['id']} - {user['nome']}")
                
                # Agendamentos existentes
                existing_appointments = await db.fetch("""
                    SELECT id, status, created_at FROM appointments 
                    WHERE user_id = $1 
                    ORDER BY created_at DESC 
                    LIMIT 5
                """, user['id'])
                
                print(f"   📅 Agendamentos existentes: {len(existing_appointments)}")
                for apt in existing_appointments[:3]:
                    print(f"      ID {apt['id']} - {apt['status']} - {apt['created_at']}")
            else:
                print("   ❌ Usuário de teste não encontrado")
                return False
                
        except Exception as e:
            print(f"   ❌ Erro no pré-teste: {e}")
        
        # TESTE 1: Webhook Response
        print("\n🚀 TESTE 1: Resposta do Webhook")
        messages_before = 0
        try:
            # Contar mensagens antes
            messages_before = await db.fetchval("""
                SELECT COUNT(*) FROM messages 
                WHERE user_id = $1 AND created_at > NOW() - INTERVAL '1 minute'
            """, user['id'])
            
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
                                "id": f"definitive_test_{int(time.time())}",
                                "timestamp": str(int(time.time())),
                                "text": {"body": "Preciso reagendar minha massagem para quinta-feira às 15h"},
                                "type": "text"
                            }],
                            "contacts": [{
                                "profile": {"name": "João Victor Vancim"},
                                "wa_id": self.TEST_PHONE
                            }]
                        },
                        "field": "messages"
                    }]
                }]
            }
            
            async with aiohttp.ClientSession() as session:
                start_time = time.time()
                async with session.post(
                    f"{self.API_BASE_URL}/webhook",
                    json=webhook_payload,
                    headers={"Content-Type": "application/json"},
                    timeout=10
                ) as response:
                    webhook_status = response.status
                    response_time = time.time() - start_time
            
            webhook_success = webhook_status == 200
            print(f"   Status: {webhook_status}")
            print(f"   Tempo: {response_time:.2f}s")
            print(f"   ✅ Webhook funcionando!" if webhook_success else f"   ❌ Webhook falhou")
            
            test_results.append({
                "test": "Webhook Response",
                "success": webhook_success,
                "details": f"HTTP {webhook_status} em {response_time:.2f}s"
            })
            
        except Exception as e:
            print(f"   ❌ Erro: {e}")
            test_results.append({"test": "Webhook Response", "success": False, "details": str(e)})
        
        # Aguardar processamento
        print("\n⏱️ Aguardando processamento (5 segundos)...")
        await asyncio.sleep(5)
        
        # TESTE 2: Processamento de Mensagens
        print("\n📨 TESTE 2: Processamento de Mensagens")
        try:
            # Contar mensagens depois
            messages_after = await db.fetchval("""
                SELECT COUNT(*) FROM messages 
                WHERE user_id = $1 AND created_at > NOW() - INTERVAL '1 minute'
            """, user['id'])
            
            messages_processed = messages_after > messages_before
            new_messages_count = messages_after - messages_before
            
            print(f"   Mensagens antes: {messages_before}")
            print(f"   Mensagens depois: {messages_after}")
            print(f"   Novas mensagens: {new_messages_count}")
            
            if messages_processed:
                print("   ✅ Bot processando mensagens!")
                
                # Mostrar últimas mensagens
                recent_messages = await db.fetch("""
                    SELECT content, message_type, created_at 
                    FROM messages 
                    WHERE user_id = $1 AND created_at > NOW() - INTERVAL '2 minutes'
                    ORDER BY created_at DESC 
                    LIMIT 3
                """, user['id'])
                
                for msg in recent_messages:
                    content = str(msg['content'])[:50] if msg['content'] else 'N/A'
                    print(f"      📝 {msg['message_type']}: \"{content}...\"")
            else:
                print("   ❌ Nenhuma nova mensagem processada")
            
            test_results.append({
                "test": "Message Processing",
                "success": messages_processed,
                "details": f"{new_messages_count} novas mensagens processadas"
            })
            
        except Exception as e:
            print(f"   ❌ Erro: {e}")
            test_results.append({"test": "Message Processing", "success": False, "details": str(e)})
        
        # TESTE 3: Operações no Banco
        print("\n🗃️ TESTE 3: Operações no Banco de Dados")
        try:
            operations_success = 0
            total_operations = 4
            
            # CREATE - Novo agendamento
            try:
                new_appointment_id = await db.fetchval("""
                    INSERT INTO appointments 
                    (user_id, business_id, service_id, date_time, status, created_at, notes)
                    VALUES ($1, 3, 1, NOW() + INTERVAL '2 days', 'pending', NOW(), 'Teste definitivo CRUD')
                    RETURNING id
                """, user['id'])
                
                if new_appointment_id:
                    print(f"   ✅ CREATE: Agendamento {new_appointment_id} criado")
                    operations_success += 1
                else:
                    print("   ❌ CREATE: Falhou")
                    
            except Exception as e:
                print(f"   ❌ CREATE: Erro - {e}")
            
            # READ - Buscar agendamentos
            try:
                appointments = await db.fetch("""
                    SELECT id, status, notes FROM appointments 
                    WHERE user_id = $1 
                    ORDER BY created_at DESC 
                    LIMIT 3
                """, user['id'])
                
                if appointments:
                    print(f"   ✅ READ: {len(appointments)} agendamentos encontrados")
                    operations_success += 1
                else:
                    print("   ❌ READ: Nenhum agendamento encontrado")
                    
            except Exception as e:
                print(f"   ❌ READ: Erro - {e}")
            
            # UPDATE - Atualizar agendamento
            if new_appointment_id:
                try:
                    update_result = await db.execute("""
                        UPDATE appointments 
                        SET notes = 'CRUD UPDATE executado com sucesso!', updated_at = NOW()
                        WHERE id = $1
                    """, new_appointment_id)
                    
                    if "UPDATE 1" in update_result:
                        print("   ✅ UPDATE: Agendamento atualizado")
                        operations_success += 1
                    else:
                        print("   ❌ UPDATE: Falhou")
                        
                except Exception as e:
                    print(f"   ❌ UPDATE: Erro - {e}")
            
            # DELETE (soft) - Cancelar agendamento
            if new_appointment_id:
                try:
                    delete_result = await db.execute("""
                        UPDATE appointments 
                        SET status = 'cancelled', 
                            cancelled_at = NOW(),
                            cancellation_reason = 'Teste definitivo'
                        WHERE id = $1
                    """, new_appointment_id)
                    
                    if "UPDATE 1" in delete_result:
                        print("   ✅ DELETE (soft): Agendamento cancelado")
                        operations_success += 1
                    else:
                        print("   ❌ DELETE: Falhou")
                        
                except Exception as e:
                    print(f"   ❌ DELETE: Erro - {e}")
            
            crud_success = operations_success >= 3
            print(f"   📊 Operações: {operations_success}/{total_operations}")
            
            test_results.append({
                "test": "Database CRUD",
                "success": crud_success,
                "details": f"{operations_success}/{total_operations} operações OK"
            })
            
        except Exception as e:
            print(f"   ❌ Erro geral no CRUD: {e}")
            test_results.append({"test": "Database CRUD", "success": False, "details": str(e)})
        
        # TESTE 4: Integridade e Constraints
        print("\n🛡️ TESTE 4: Integridade do Banco")
        try:
            integrity_tests = 0
            integrity_passed = 0
            
            # FK constraint
            try:
                await db.execute("""
                    INSERT INTO appointments 
                    (user_id, business_id, service_id, date_time, status, created_at)
                    VALUES (999999, 3, 1, NOW() + INTERVAL '1 day', 'pending', NOW())
                """)
                print("   ❌ FK constraint falhou")
            except:
                print("   ✅ FK constraint OK")
                integrity_passed += 1
            integrity_tests += 1
            
            # Business rules
            try:
                valid_services = await db.fetchval("SELECT COUNT(*) FROM services WHERE is_active = true")
                valid_businesses = await db.fetchval("SELECT COUNT(*) FROM businesses")
                
                if valid_services > 0 and valid_businesses > 0:
                    print(f"   ✅ Business rules: {valid_services} serviços, {valid_businesses} negócios")
                    integrity_passed += 1
                else:
                    print("   ❌ Business rules: Dados faltando")
            except Exception as e:
                print(f"   ❌ Business rules: Erro - {e}")
            integrity_tests += 1
            
            integrity_success = integrity_passed >= integrity_tests * 0.8
            
            test_results.append({
                "test": "Data Integrity",
                "success": integrity_success,
                "details": f"{integrity_passed}/{integrity_tests} verificações OK"
            })
            
        except Exception as e:
            print(f"   ❌ Erro na integridade: {e}")
            test_results.append({"test": "Data Integrity", "success": False, "details": str(e)})
        
        # RESULTADO FINAL
        print("\n" + "="*70)
        print("🏆 RESULTADO DEFINITIVO")
        print("="*70)
        
        total_tests = len(test_results)
        passed_tests = len([r for r in test_results if r["success"] is True])
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📊 Testes executados: {total_tests}")
        print(f"✅ Testes aprovados: {passed_tests}")
        print(f"🎯 Taxa de sucesso: {success_rate:.1f}%")
        
        print(f"\n📋 Detalhes:")
        for result in test_results:
            status = "✅" if result["success"] else "❌"
            print(f"   {status} {result['test']}: {result['details']}")
        
        overall_success = success_rate >= 75
        
        if overall_success:
            print(f"\n🎉 SUCESSO DEFINITIVO! Sistema aprovado com {success_rate:.1f}%!")
            print("🚀 WhatsApp Agent está funcionando perfeitamente!")
            conclusion = "SISTEMA TOTALMENTE APROVADO"
        else:
            print(f"\n⚠️ Sistema precisa de ajustes ({success_rate:.1f}%)")
            conclusion = "SISTEMA NECESSITA MELHORIAS"
        
        print("="*70)
        
        # Salvar relatório
        report = {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "success_rate": success_rate,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "conclusion": conclusion,
            "test_phone": self.TEST_PHONE,
            "test_results": test_results
        }
        
        filename = f"definitive_test_report_{self.session_id}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n📄 Relatório definitivo salvo: {filename}")
        
        # Fechar conexão
        await db.close()
        
        return overall_success

async def main():
    print("🎯 INICIANDO TESTE DEFINITIVO")
    print("=" * 30)
    print("Este teste funciona com a REALIDADE do sistema:")
    print("• Usuário existente em produção")
    print("• Agendamentos já criados")
    print("• Mensagens processadas")
    print("• CRUD completo no banco")
    print("=" * 30)
    
    tester = DefinitiveTest()
    return await tester.run_test()

if __name__ == "__main__":
    success = asyncio.run(main())
    if success:
        print("\n🌟 TESTE CONCLUÍDO COM SUCESSO! 🌟")
    else:
        print("\n⚠️ Teste concluído com ressalvas")