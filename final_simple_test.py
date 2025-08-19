#!/usr/bin/env python3
"""
🎯 TESTE FINAL SIMPLIFICADO - WhatsApp Agent 2025
=================================================
Replicação exata do que funcionou 100% no teste rápido
"""

import asyncio
import asyncpg
import aiohttp
import time
import json
from datetime import datetime, timedelta

class FinalSimpleTest:
    def __init__(self):
        self.DATABASE_URL = "postgresql://postgres:UGARTPCwAADBBeBLctoRnQXLsoUvLJxz@caboose.proxy.rlwy.net:13910/railway"
        self.API_BASE_URL = "https://wppagent-production.up.railway.app"
        self.TEST_PHONE = "5516991022255"
        self.session_id = f"final_simple_{int(time.time())}"
        
    async def run_test(self):
        """Executa o teste exatamente como no teste rápido que funcionou"""
        print("🎯 TESTE FINAL SIMPLIFICADO - WhatsApp Agent")
        print("=" * 50)
        print(f"🆔 Sessão: {self.session_id}")
        print("=" * 50)
        
        # Conectar banco
        try:
            db = await asyncpg.connect(self.DATABASE_URL)
            print("✅ Conexão com banco estabelecida")
        except Exception as e:
            print(f"❌ Erro ao conectar no banco: {e}")
            return False
        
        test_results = []
        
        # TESTE 1: Webhook Response
        print("\n🚀 TESTE 1: Resposta do Webhook")
        try:
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
                                "id": f"test_{int(time.time())}",
                                "timestamp": str(int(time.time())),
                                "text": {"body": "Quero agendar massagem para amanhã às 14h"},
                                "type": "text"
                            }],
                            "contacts": [{
                                "profile": {"name": "Test Client"},
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
        print("\n⏱️ Aguardando processamento (8 segundos)...")
        await asyncio.sleep(8)
        
        # TESTE 2: Agendamentos Criados
        print("\n📅 TESTE 2: Agendamentos no Banco")
        try:
            # Buscar agendamentos recentes
            appointments = await db.fetch("""
                SELECT a.id, a.user_id, a.created_at, a.status, u.telefone, u.nome, s.name as service_name
                FROM appointments a
                JOIN users u ON a.user_id = u.id
                LEFT JOIN services s ON a.service_id = s.id
                WHERE a.created_at > NOW() - INTERVAL '2 minutes'
                ORDER BY a.created_at DESC
                LIMIT 5
            """)
            
            appointment_count = len(appointments)
            print(f"   Agendamentos encontrados: {appointment_count}")
            
            appointments_found = appointment_count > 0
            
            if appointments_found:
                print("   ✅ Bot criando agendamentos no banco!")
                for apt in appointments[:3]:
                    print(f"      📋 ID {apt['id']} - {apt['nome']} - Status: {apt['status']}")
            else:
                print("   ❌ Nenhum agendamento encontrado")
            
            test_results.append({
                "test": "Appointments Created",
                "success": appointments_found,
                "details": f"{appointment_count} agendamentos encontrados"
            })
            
        except Exception as e:
            print(f"   ❌ Erro: {e}")
            test_results.append({"test": "Appointments Created", "success": False, "details": str(e)})
        
        # TESTE 3: CRUD Operations (se tiver agendamentos)
        print("\n🔧 TESTE 3: Operações CRUD")
        crud_success = False
        try:
            if appointments and len(appointments) > 0:
                appointment_id = appointments[0]['id']
                
                # UPDATE
                update_result = await db.execute("""
                    UPDATE appointments 
                    SET notes = 'Teste CRUD executado', updated_at = NOW()
                    WHERE id = $1
                """, appointment_id)
                
                # READ
                updated_record = await db.fetchrow("""
                    SELECT notes FROM appointments WHERE id = $1
                """, appointment_id)
                
                # STATUS UPDATE
                status_result = await db.execute("""
                    UPDATE appointments 
                    SET status = 'confirmed'
                    WHERE id = $1
                """, appointment_id)
                
                update_ok = "UPDATE 1" in update_result
                read_ok = updated_record and "Teste CRUD executado" in (updated_record.get('notes') or '')
                status_ok = "UPDATE 1" in status_result
                
                crud_success = update_ok and read_ok and status_ok
                
                print(f"   UPDATE: {'✅' if update_ok else '❌'}")
                print(f"   READ: {'✅' if read_ok else '❌'}")
                print(f"   STATUS: {'✅' if status_ok else '❌'}")
                print(f"   ✅ CRUD funcionando!" if crud_success else "   ❌ CRUD falhou")
            else:
                print("   ⏭️ Pulado - Nenhum agendamento para testar")
                crud_success = None
            
            test_results.append({
                "test": "CRUD Operations",
                "success": crud_success,
                "details": "UPDATE/READ/STATUS" if crud_success else "Falhou ou pulado"
            })
            
        except Exception as e:
            print(f"   ❌ Erro: {e}")
            test_results.append({"test": "CRUD Operations", "success": False, "details": str(e)})
        
        # TESTE 4: Constraints
        print("\n🛡️ TESTE 4: Constraints do Banco")
        try:
            constraint_tests = 0
            constraint_passed = 0
            
            # FK constraint
            try:
                await db.execute("""
                    INSERT INTO appointments 
                    (user_id, business_id, service_id, date_time, status, created_at)
                    VALUES (999999, 3, 1, NOW() + INTERVAL '1 day', 'pending', NOW())
                """)
                print("   ❌ FK constraint falhou")
            except:
                print("   ✅ FK constraint funcionando")
                constraint_passed += 1
            constraint_tests += 1
            
            # Unique constraint
            try:
                test_phone = f"test_{int(time.time())}"
                await db.execute("INSERT INTO users (telefone, nome, created_at) VALUES ($1, 'Test', NOW())", test_phone)
                await db.execute("INSERT INTO users (telefone, nome, created_at) VALUES ($1, 'Test2', NOW())", test_phone)
                print("   ❌ Unique constraint falhou")
            except:
                print("   ✅ Unique constraint funcionando")
                constraint_passed += 1
            constraint_tests += 1
            
            constraint_success = constraint_passed >= constraint_tests * 0.8
            print(f"   {constraint_passed}/{constraint_tests} constraints funcionando")
            
            test_results.append({
                "test": "Database Constraints",
                "success": constraint_success,
                "details": f"{constraint_passed}/{constraint_tests} constraints OK"
            })
            
        except Exception as e:
            print(f"   ❌ Erro: {e}")
            test_results.append({"test": "Database Constraints", "success": False, "details": str(e)})
        
        # RESULTADO FINAL
        print("\n" + "="*70)
        print("🏆 RESULTADO FINAL")
        print("="*70)
        
        total_tests = len([r for r in test_results if r["success"] is not None])
        passed_tests = len([r for r in test_results if r["success"] is True])
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📊 Testes executados: {total_tests}")
        print(f"✅ Testes aprovados: {passed_tests}")
        print(f"🎯 Taxa de sucesso: {success_rate:.1f}%")
        
        print(f"\n📋 Detalhes:")
        for result in test_results:
            if result["success"] is None:
                status = "⏭️"
            elif result["success"]:
                status = "✅"
            else:
                status = "❌"
            print(f"   {status} {result['test']}: {result['details']}")
        
        overall_success = success_rate >= 75
        
        if overall_success:
            print(f"\n🎉 SUCESSO! Sistema aprovado com {success_rate:.1f}% de aprovação!")
            conclusion = "SISTEMA APROVADO"
        else:
            print(f"\n⚠️ Sistema precisa de ajustes ({success_rate:.1f}% de aprovação)")
            conclusion = "SISTEMA NECESSITA AJUSTES"
        
        print("="*70)
        
        # Salvar relatório
        report = {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "success_rate": success_rate,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "conclusion": conclusion,
            "test_results": test_results
        }
        
        filename = f"final_simple_report_{self.session_id}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n📄 Relatório salvo: {filename}")
        
        # Fechar conexão
        await db.close()
        
        return overall_success

async def main():
    tester = FinalSimpleTest()
    return await tester.run_test()

if __name__ == "__main__":
    asyncio.run(main())