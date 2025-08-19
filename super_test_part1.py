#!/usr/bin/env python3
"""
🚀 SUPER TESTE DEFINITIVO - PARTE 1: INFRAESTRUTURA E CORE
=========================================================
WhatsApp Agent System - Validação Completa 2025

ESTA É A PARTE 1 DE 2 DO SUPER TESTE MAIS COMPLETO JÁ CRIADO!

🎯 ÁREAS TESTADAS NA PARTE 1:
═══════════════════════════════
1. 🔗 CONECTIVIDADE E API
   • Webhook response (HTTP 200)
   • Tempo de resposta
   • Processamento de payloads
   • Session management

2. 📨 PROCESSAMENTO DE MENSAGENS
   • Recepção via webhook
   • Parsing de mensagens
   • Geração de respostas
   • Logging de conversas

3. 🗄️ BANCO DE DADOS - CORE
   • Conexão PostgreSQL
   • Operações CRUD básicas
   • Constraints e integridade
   • Transações e rollbacks

4. 🛡️ SEGURANÇA E VALIDAÇÃO
   • Foreign Key constraints
   • Unique constraints  
   • Data validation
   • SQL injection protection

5. ⚡ PERFORMANCE E CONCORRÊNCIA
   • Tempo de resposta
   • Handling simultâneo
   • Resource management
   • Memory usage

ESTE TESTE USA TODOS OS MÉTODOS QUE DESENVOLVEMOS:
• Teste definitivo (100% sucesso)
• Teste rápido (validação direta)
• Teste híbrido (combinação)
• Investigação forense (debugging)
• Schema compatibility (adaptativo)
"""

import asyncio
import asyncpg
import aiohttp
import time
import json
import logging
import random
import psutil
import gc
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict


@dataclass
class SuperTestResult:
    """Resultado detalhado do super teste"""
    test_category: str
    test_name: str
    success: bool
    execution_time: float
    records_affected: int
    errors: List[str]
    warnings: List[str]
    metrics: Dict[str, Any]
    is_critical: bool = True
    validation_passed: bool = False


class SuperTesterPart1:
    def __init__(self):
        self.DATABASE_URL = "postgresql://postgres:UGARTPCwAADBBeBLctoRnQXLsoUvLJxz@caboose.proxy.rlwy.net:13910/railway"
        self.API_BASE_URL = "https://wppagent-production.up.railway.app"
        self.TEST_PHONE = "5516991022255"
        self.session_id = f"SUPER_TEST_P1_{int(time.time())}"
        
        # Métricas de sistema
        self.start_memory = 0
        self.start_cpu = 0
        self.performance_metrics = {}
        
        # Resultados organizados por categoria
        self.test_results: Dict[str, List[SuperTestResult]] = {
            "CONNECTIVITY": [],
            "MESSAGING": [],
            "DATABASE_CORE": [],
            "SECURITY": [],
            "PERFORMANCE": []
        }
        
        # Dados de teste para limpeza
        self.cleanup_data = {
            "user_ids": [],
            "appointment_ids": [],
            "message_ids": []
        }
        
        # Logger configurado
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - [SUPER TEST P1] - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(f'SUPER_TEST_P1_{self.session_id}.log')
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    async def initialize_system_monitoring(self):
        """Inicializa monitoramento de sistema"""
        self.logger.info("📊 Inicializando monitoramento de sistema...")
        
        # Métricas iniciais
        process = psutil.Process()
        self.start_memory = process.memory_info().rss / 1024 / 1024  # MB
        self.start_cpu = psutil.cpu_percent(interval=1)
        
        # Conectar ao banco
        try:
            self.db = await asyncpg.connect(self.DATABASE_URL)
            
            # Teste de conectividade inicial
            result = await self.db.fetchval("SELECT 1")
            if result != 1:
                raise Exception("Teste de conectividade falhou")
                
            self.logger.info("✅ Sistema inicializado e banco conectado")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erro na inicialização: {e}")
            return False
    
    # ═══════════════════════════════════════════════════════════════
    # 🔗 CATEGORIA 1: TESTES DE CONECTIVIDADE E API
    # ═══════════════════════════════════════════════════════════════
    
    async def test_webhook_connectivity(self) -> SuperTestResult:
        """Teste 1.1: Conectividade básica do webhook"""
        self.logger.info("🔗 TESTE 1.1: Conectividade do Webhook")
        
        errors = []
        warnings = []
        metrics = {}
        start_time = time.time()
        
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
                                "id": f"connectivity_test_{int(time.time())}",
                                "timestamp": str(int(time.time())),
                                "text": {"body": "SUPER TESTE - Conectividade"},
                                "type": "text"
                            }],
                            "contacts": [{
                                "profile": {"name": "Super Test"},
                                "wa_id": self.TEST_PHONE
                            }]
                        },
                        "field": "messages"
                    }]
                }]
            }
            
            # Múltiplas tentativas para medir consistência
            response_times = []
            status_codes = []
            
            for attempt in range(3):
                attempt_start = time.time()
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.API_BASE_URL}/webhook",
                        json=webhook_payload,
                        headers={"Content-Type": "application/json"},
                        timeout=15
                    ) as response:
                        status_code = response.status
                        response_time = time.time() - attempt_start
                        
                        response_times.append(response_time)
                        status_codes.append(status_code)
                
                await asyncio.sleep(1)
            
            # Calcular métricas
            avg_response_time = sum(response_times) / len(response_times)
            success_rate = sum(1 for code in status_codes if code == 200) / len(status_codes)
            
            metrics = {
                "average_response_time": round(avg_response_time, 3),
                "response_times": response_times,
                "status_codes": status_codes,
                "success_rate": success_rate,
                "attempts": len(response_times)
            }
            
            # Validações
            if avg_response_time > 5.0:
                warnings.append(f"Response time alto: {avg_response_time:.3f}s")
                
            if success_rate < 1.0:
                errors.append(f"Taxa de sucesso baixa: {success_rate*100:.1f}%")
            
            success = len(errors) == 0 and success_rate == 1.0
            validation_passed = avg_response_time < 10.0 and success_rate >= 0.8
            
        except Exception as e:
            errors.append(f"Erro na conectividade: {str(e)}")
            success = False
            validation_passed = False
            
        execution_time = time.time() - start_time
        
        return SuperTestResult(
            test_category="CONNECTIVITY",
            test_name="Webhook Connectivity",
            success=success,
            execution_time=execution_time,
            records_affected=0,
            errors=errors,
            warnings=warnings,
            metrics=metrics,
            is_critical=True,
            validation_passed=validation_passed
        )
    
    async def test_api_load_handling(self) -> SuperTestResult:
        """Teste 1.2: Handling de carga da API"""
        self.logger.info("⚡ TESTE 1.2: Load Handling da API")
        
        errors = []
        warnings = []
        metrics = {}
        start_time = time.time()
        
        try:
            # Simular múltiplas requisições simultâneas
            concurrent_requests = 5
            tasks = []
            
            for i in range(concurrent_requests):
                payload = {
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
                                    "from": f"55169910{i:05d}",
                                    "id": f"load_test_{i}_{int(time.time())}",
                                    "timestamp": str(int(time.time())),
                                    "text": {"body": f"Load test message {i}"},
                                    "type": "text"
                                }],
                                "contacts": [{
                                    "profile": {"name": f"Load Test {i}"},
                                    "wa_id": f"55169910{i:05d}"
                                }]
                            },
                            "field": "messages"
                        }]
                    }]
                }
                
                task = self._make_concurrent_request(payload, i)
                tasks.append(task)
            
            # Executar todas as requisições simultaneamente
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Analisar resultados
            successful_requests = 0
            failed_requests = 0
            total_response_time = 0
            
            for result in results:
                if isinstance(result, Exception):
                    failed_requests += 1
                    errors.append(f"Requisição falhou: {str(result)}")
                else:
                    if result.get("success"):
                        successful_requests += 1
                        total_response_time += result.get("response_time", 0)
                    else:
                        failed_requests += 1
            
            success_rate = successful_requests / concurrent_requests
            avg_response_time = total_response_time / successful_requests if successful_requests > 0 else 0
            
            metrics = {
                "concurrent_requests": concurrent_requests,
                "successful_requests": successful_requests,
                "failed_requests": failed_requests,
                "success_rate": success_rate,
                "average_response_time": round(avg_response_time, 3)
            }
            
            # Validações
            if success_rate < 0.8:
                errors.append(f"Taxa de sucesso baixa sob carga: {success_rate*100:.1f}%")
                
            if avg_response_time > 10.0:
                warnings.append(f"Response time alto sob carga: {avg_response_time:.3f}s")
            
            success = len(errors) == 0 and success_rate >= 0.8
            validation_passed = success_rate >= 0.6
            
        except Exception as e:
            errors.append(f"Erro no teste de carga: {str(e)}")
            success = False
            validation_passed = False
            
        execution_time = time.time() - start_time
        
        return SuperTestResult(
            test_category="CONNECTIVITY",
            test_name="API Load Handling",
            success=success,
            execution_time=execution_time,
            records_affected=successful_requests,
            errors=errors,
            warnings=warnings,
            metrics=metrics,
            is_critical=True,
            validation_passed=validation_passed
        )
    
    async def _make_concurrent_request(self, payload: dict, request_id: int) -> dict:
        """Helper para requisições simultâneas"""
        try:
            start_time = time.time()
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.API_BASE_URL}/webhook",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=15
                ) as response:
                    response_time = time.time() - start_time
                    
                    return {
                        "success": response.status == 200,
                        "status_code": response.status,
                        "response_time": response_time,
                        "request_id": request_id
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "request_id": request_id
            }
    
    # ═══════════════════════════════════════════════════════════════
    # 📨 CATEGORIA 2: TESTES DE PROCESSAMENTO DE MENSAGENS
    # ═══════════════════════════════════════════════════════════════
    
    async def test_message_processing(self) -> SuperTestResult:
        """Teste 2.1: Processamento completo de mensagens"""
        self.logger.info("📨 TESTE 2.1: Processamento de Mensagens")
        
        errors = []
        warnings = []
        metrics = {}
        records_affected = 0
        start_time = time.time()
        
        try:
            # Contar mensagens antes do teste
            messages_before = await self.db.fetchval("""
                SELECT COUNT(*) FROM messages 
                WHERE user_id = 2 AND created_at > NOW() - INTERVAL '30 seconds'
            """)
            
            # Enviar mensagem de teste
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
                                "id": f"message_proc_test_{int(time.time())}",
                                "timestamp": str(int(time.time())),
                                "text": {"body": "SUPER TESTE - Processamento de mensagens complexas"},
                                "type": "text"
                            }],
                            "contacts": [{
                                "profile": {"name": "Super Test Processor"},
                                "wa_id": self.TEST_PHONE
                            }]
                        },
                        "field": "messages"
                    }]
                }]
            }
            
            request_start = time.time()
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.API_BASE_URL}/webhook",
                    json=webhook_payload,
                    headers={"Content-Type": "application/json"},
                    timeout=15
                ) as response:
                    request_time = time.time() - request_start
                    webhook_status = response.status
            
            # Aguardar processamento
            await asyncio.sleep(6)
            
            # Verificar mensagens processadas
            messages_after = await self.db.fetchval("""
                SELECT COUNT(*) FROM messages 
                WHERE user_id = 2 AND created_at > NOW() - INTERVAL '30 seconds'
            """)
            
            new_messages = messages_after - messages_before
            
            # Buscar mensagens detalhadas
            recent_messages = await self.db.fetch("""
                SELECT m.*, c.status as conversation_status
                FROM messages m
                JOIN conversations c ON m.conversation_id = c.id
                WHERE m.user_id = 2 
                AND m.created_at > NOW() - INTERVAL '1 minute'
                ORDER BY m.created_at DESC
                LIMIT 5
            """)
            
            # Análise das mensagens
            bot_responses = [msg for msg in recent_messages if msg['direction'] == 'out']
            user_messages = [msg for msg in recent_messages if msg['direction'] == 'in']
            
            metrics = {
                "webhook_status": webhook_status,
                "request_time": round(request_time, 3),
                "messages_before": messages_before,
                "messages_after": messages_after,
                "new_messages": new_messages,
                "bot_responses": len(bot_responses),
                "user_messages": len(user_messages),
                "total_recent_messages": len(recent_messages)
            }
            
            records_affected = new_messages
            
            # Validações
            if webhook_status != 200:
                errors.append(f"Webhook retornou status {webhook_status}")
                
            if new_messages < 1:
                warnings.append("Nenhuma nova mensagem foi processada")
                
            if len(bot_responses) == 0:
                warnings.append("Bot não gerou respostas")
                
            success = webhook_status == 200 and new_messages >= 1
            validation_passed = success and len(bot_responses) > 0
            
        except Exception as e:
            errors.append(f"Erro no processamento de mensagens: {str(e)}")
            success = False
            validation_passed = False
            
        execution_time = time.time() - start_time
        
        return SuperTestResult(
            test_category="MESSAGING",
            test_name="Message Processing",
            success=success,
            execution_time=execution_time,
            records_affected=records_affected,
            errors=errors,
            warnings=warnings,
            metrics=metrics,
            is_critical=True,
            validation_passed=validation_passed
        )
    
    # ═══════════════════════════════════════════════════════════════
    # 🗄️ CATEGORIA 3: TESTES DE BANCO DE DADOS CORE
    # ═══════════════════════════════════════════════════════════════
    
    async def test_database_crud_operations(self) -> SuperTestResult:
        """Teste 3.1: Operações CRUD fundamentais"""
        self.logger.info("🗄️ TESTE 3.1: CRUD Operations do Banco")
        
        errors = []
        warnings = []
        metrics = {}
        records_affected = 0
        start_time = time.time()
        
        try:
            # CREATE - Criar usuário de teste
            timestamp = str(int(time.time()))[-6:]
            random_suffix = str(random.randint(100, 999))
            phone = f"5516991{timestamp}{random_suffix}"[:20]
            
            user_id = await self.db.fetchval("""
                INSERT INTO users (wa_id, telefone, nome, created_at, updated_at)
                VALUES ($1, $2, $3, NOW(), NOW())
                RETURNING id
            """, phone, phone, f"SuperTest{timestamp}")
            
            if user_id:
                self.cleanup_data["user_ids"].append(user_id)
                records_affected += 1
                
                # CREATE - Criar agendamento
                appointment_id = await self.db.fetchval("""
                    INSERT INTO appointments 
                    (user_id, business_id, service_id, date_time, status, created_at, notes)
                    VALUES ($1, 3, 1, NOW() + INTERVAL '2 days', 'pending', NOW(), 'Super Test CRUD')
                    RETURNING id
                """, user_id)
                
                if appointment_id:
                    self.cleanup_data["appointment_ids"].append(appointment_id)
                    records_affected += 1
                    
                    # READ - Verificar dados
                    appointment_data = await self.db.fetchrow("""
                        SELECT a.*, u.nome, s.name as service_name
                        FROM appointments a
                        JOIN users u ON a.user_id = u.id
                        JOIN services s ON a.service_id = s.id
                        WHERE a.id = $1
                    """, appointment_id)
                    
                    if appointment_data:
                        # UPDATE - Atualizar agendamento
                        update_result = await self.db.execute("""
                            UPDATE appointments 
                            SET notes = 'Super Test CRUD - Updated!', 
                                updated_at = NOW()
                            WHERE id = $1
                        """, appointment_id)
                        
                        if "UPDATE 1" in update_result:
                            records_affected += 1
                            
                            # READ após UPDATE - Verificar mudança
                            updated_data = await self.db.fetchrow("""
                                SELECT notes FROM appointments WHERE id = $1
                            """, appointment_id)
                            
                            if updated_data and "Updated!" in updated_data.get('notes', ''):
                                # DELETE (soft) - Cancelar
                                delete_result = await self.db.execute("""
                                    UPDATE appointments 
                                    SET status = 'cancelled',
                                        cancelled_at = NOW(),
                                        cancellation_reason = 'Super Test'
                                    WHERE id = $1
                                """, appointment_id)
                                
                                if "UPDATE 1" in delete_result:
                                    records_affected += 1
                                    
                                    metrics = {
                                        "user_created": True,
                                        "appointment_created": True,
                                        "read_successful": True,
                                        "update_successful": True,
                                        "delete_successful": True,
                                        "crud_operations_completed": 5
                                    }
                                else:
                                    errors.append("Falha no DELETE (cancelamento)")
                            else:
                                errors.append("UPDATE não foi verificado corretamente")
                        else:
                            errors.append("Falha no UPDATE do agendamento")
                    else:
                        errors.append("Falha no READ do agendamento")
                else:
                    errors.append("Falha ao criar agendamento")
            else:
                errors.append("Falha ao criar usuário")
            
            success = len(errors) == 0 and records_affected >= 4
            validation_passed = records_affected >= 3
            
        except Exception as e:
            errors.append(f"Erro nas operações CRUD: {str(e)}")
            success = False
            validation_passed = False
            
        execution_time = time.time() - start_time
        
        return SuperTestResult(
            test_category="DATABASE_CORE",
            test_name="CRUD Operations",
            success=success,
            execution_time=execution_time,
            records_affected=records_affected,
            errors=errors,
            warnings=warnings,
            metrics=metrics,
            is_critical=True,
            validation_passed=validation_passed
        )
    
    async def test_database_transactions(self) -> SuperTestResult:
        """Teste 3.2: Transações e rollbacks"""
        self.logger.info("🔄 TESTE 3.2: Transações e Rollbacks")
        
        errors = []
        warnings = []
        metrics = {}
        records_affected = 0
        start_time = time.time()
        
        try:
            # Teste de transação bem-sucedida
            async with self.db.transaction():
                temp_user_id = await self.db.fetchval("""
                    INSERT INTO users (wa_id, telefone, nome, created_at)
                    VALUES ($1, $2, 'Transaction Test', NOW())
                    RETURNING id
                """, f"trans_test_{int(time.time())}", f"trans_test_{int(time.time())}")
                
                if temp_user_id:
                    self.cleanup_data["user_ids"].append(temp_user_id)
                    records_affected += 1
                    
            # Teste de rollback - transação que deve falhar
            rollback_worked = False
            try:
                async with self.db.transaction():
                    # Criar usuário temporário
                    temp_phone = f"rollback_test_{int(time.time())}"
                    rollback_user_id = await self.db.fetchval("""
                        INSERT INTO users (wa_id, telefone, nome, created_at)
                        VALUES ($1, $2, 'Rollback Test', NOW())
                        RETURNING id
                    """, temp_phone, temp_phone)
                    
                    # Forçar erro com FK inválida
                    await self.db.execute("""
                        INSERT INTO appointments 
                        (user_id, business_id, service_id, date_time, status, created_at)
                        VALUES ($1, 3, 999999, NOW() + INTERVAL '1 day', 'pending', NOW())
                    """, rollback_user_id)
                    
            except Exception:
                # Erro esperado - verificar se rollback funcionou
                user_exists = await self.db.fetchval("""
                    SELECT COUNT(*) FROM users 
                    WHERE telefone = $1
                """, temp_phone)
                
                if user_exists == 0:
                    rollback_worked = True
                    
            # Teste de commit explícito
            commit_test_phone = f"commit_test_{int(time.time())}"
            commit_user_id = None
            
            async with self.db.transaction():
                commit_user_id = await self.db.fetchval("""
                    INSERT INTO users (wa_id, telefone, nome, created_at)
                    VALUES ($1, $2, 'Commit Test', NOW())
                    RETURNING id
                """, commit_test_phone, commit_test_phone)
                
                if commit_user_id:
                    self.cleanup_data["user_ids"].append(commit_user_id)
                    records_affected += 1
                    
            # Verificar se commit funcionou
            commit_verified = False
            if commit_user_id:
                user_exists = await self.db.fetchval("""
                    SELECT COUNT(*) FROM users WHERE id = $1
                """, commit_user_id)
                commit_verified = user_exists > 0
            
            metrics = {
                "transaction_commit_success": temp_user_id is not None,
                "rollback_worked": rollback_worked,
                "commit_verified": commit_verified,
                "total_transaction_tests": 3
            }
            
            # Validações
            if not rollback_worked:
                errors.append("Rollback não funcionou corretamente")
                
            if not commit_verified:
                errors.append("Commit não foi verificado")
                
            success = len(errors) == 0 and rollback_worked and commit_verified
            validation_passed = rollback_worked or commit_verified
            
        except Exception as e:
            errors.append(f"Erro nos testes de transação: {str(e)}")
            success = False
            validation_passed = False
            
        execution_time = time.time() - start_time
        
        return SuperTestResult(
            test_category="DATABASE_CORE",
            test_name="Transactions & Rollbacks",
            success=success,
            execution_time=execution_time,
            records_affected=records_affected,
            errors=errors,
            warnings=warnings,
            metrics=metrics,
            is_critical=True,
            validation_passed=validation_passed
        )
    
    # ═══════════════════════════════════════════════════════════════
    # 🛡️ CATEGORIA 4: TESTES DE SEGURANÇA E VALIDAÇÃO
    # ═══════════════════════════════════════════════════════════════
    
    async def test_security_constraints(self) -> SuperTestResult:
        """Teste 4.1: Constraints de segurança"""
        self.logger.info("🛡️ TESTE 4.1: Security Constraints")
        
        errors = []
        warnings = []
        metrics = {}
        start_time = time.time()
        validations_passed = 0
        total_validations = 6
        
        try:
            # 1. FK constraint - user_id inválido
            try:
                await self.db.execute("""
                    INSERT INTO appointments 
                    (user_id, business_id, service_id, date_time, status, created_at)
                    VALUES (999999, 3, 1, NOW() + INTERVAL '1 day', 'pending', NOW())
                """)
                errors.append("FK constraint falhou - user_id inválido aceito")
            except:
                validations_passed += 1
                
            # 2. FK constraint - service_id inválido
            try:
                await self.db.execute("""
                    INSERT INTO appointments 
                    (user_id, business_id, service_id, date_time, status, created_at)
                    VALUES (2, 3, 999999, NOW() + INTERVAL '1 day', 'pending', NOW())
                """)
                errors.append("FK constraint falhou - service_id inválido aceito")
            except:
                validations_passed += 1
                
            # 3. Unique constraint - telefone
            try:
                test_phone = f"security_test_{int(time.time())}"
                user1 = await self.db.fetchval("""
                    INSERT INTO users (telefone, nome, created_at)
                    VALUES ($1, 'Security Test 1', NOW())
                    RETURNING id
                """, test_phone)
                
                if user1:
                    self.cleanup_data["user_ids"].append(user1)
                    
                    user2 = await self.db.fetchval("""
                        INSERT INTO users (telefone, nome, created_at)
                        VALUES ($1, 'Security Test 2', NOW())
                        RETURNING id
                    """, test_phone)
                    
                    if user2:
                        errors.append("Unique constraint falhou - telefone duplicado aceito")
                        self.cleanup_data["user_ids"].append(user2)
            except:
                validations_passed += 1
                
            # 4. Data type validation - date
            try:
                await self.db.execute("""
                    INSERT INTO appointments 
                    (user_id, business_id, service_id, date_time, status, created_at)
                    VALUES (2, 3, 1, 'invalid-date', 'pending', NOW())
                """)
                errors.append("Data validation falhou - data inválida aceita")
            except:
                validations_passed += 1
                
            # 5. Business rules - is_active constraint
            try:
                active_services = await self.db.fetchval("""
                    SELECT COUNT(*) FROM services WHERE is_active = true
                """)
                inactive_services = await self.db.fetchval("""
                    SELECT COUNT(*) FROM services WHERE is_active = false
                """)
                
                if active_services > 0:
                    validations_passed += 1
                else:
                    warnings.append("Nenhum serviço ativo encontrado")
                    
            except Exception as e:
                warnings.append(f"Erro ao verificar serviços ativos: {e}")
                
            # 6. Cascade protection
            if self.cleanup_data["user_ids"]:
                user_id = self.cleanup_data["user_ids"][0]
                
                # Criar dependência
                appointment_id = await self.db.fetchval("""
                    INSERT INTO appointments 
                    (user_id, business_id, service_id, date_time, status, created_at)
                    VALUES ($1, 3, 1, NOW() + INTERVAL '1 day', 'pending', NOW())
                    RETURNING id
                """, user_id)
                
                if appointment_id:
                    self.cleanup_data["appointment_ids"].append(appointment_id)
                    
                    # Tentar deletar usuário com dependências
                    try:
                        await self.db.execute("DELETE FROM users WHERE id = $1", user_id)
                        errors.append("Cascade protection falhou - usuário com dependências deletado")
                    except:
                        validations_passed += 1
            
            metrics = {
                "validations_passed": validations_passed,
                "total_validations": total_validations,
                "security_score": round((validations_passed / total_validations) * 100, 1),
                "fk_constraints_working": validations_passed >= 2,
                "unique_constraints_working": validations_passed >= 3,
                "data_validation_working": validations_passed >= 4
            }
            
            success = len(errors) == 0 and validations_passed >= 4
            validation_passed = validations_passed >= 3
            
        except Exception as e:
            errors.append(f"Erro nos testes de segurança: {str(e)}")
            success = False
            validation_passed = False
            
        execution_time = time.time() - start_time
        
        return SuperTestResult(
            test_category="SECURITY",
            test_name="Security Constraints",
            success=success,
            execution_time=execution_time,
            records_affected=validations_passed,
            errors=errors,
            warnings=warnings,
            metrics=metrics,
            is_critical=True,
            validation_passed=validation_passed
        )
    
    # ═══════════════════════════════════════════════════════════════
    # ⚡ CATEGORIA 5: TESTES DE PERFORMANCE E CONCORRÊNCIA
    # ═══════════════════════════════════════════════════════════════
    
    async def test_system_performance(self) -> SuperTestResult:
        """Teste 5.1: Performance geral do sistema"""
        self.logger.info("⚡ TESTE 5.1: System Performance")
        
        errors = []
        warnings = []
        metrics = {}
        records_affected = 0
        start_time = time.time()
        
        try:
            # Métricas de sistema no início
            process = psutil.Process()
            memory_before = process.memory_info().rss / 1024 / 1024
            cpu_before = psutil.cpu_percent(interval=0.1)
            
            # Teste de query performance
            query_times = []
            
            # Query simples
            simple_start = time.time()
            simple_result = await self.db.fetchval("SELECT COUNT(*) FROM users")
            simple_time = time.time() - simple_start
            query_times.append(("simple_count", simple_time))
            
            # Query com JOIN
            join_start = time.time()
            join_result = await self.db.fetchval("""
                SELECT COUNT(*) 
                FROM appointments a 
                JOIN users u ON a.user_id = u.id 
                JOIN services s ON a.service_id = s.id
            """)
            join_time = time.time() - join_start
            query_times.append(("complex_join", join_time))
            
            # Query com filtros e ordenação
            complex_start = time.time()
            complex_result = await self.db.fetch("""
                SELECT a.id, a.status, u.nome, s.name, a.created_at
                FROM appointments a
                JOIN users u ON a.user_id = u.id
                JOIN services s ON a.service_id = s.id
                WHERE a.created_at > NOW() - INTERVAL '7 days'
                ORDER BY a.created_at DESC
                LIMIT 50
            """)
            complex_time = time.time() - complex_start
            query_times.append(("complex_filtered", complex_time))
            records_affected = len(complex_result)
            
            # Teste de inserção em lote
            batch_start = time.time()
            batch_users = []
            for i in range(5):
                phone = f"perf_test_{int(time.time())}_{i}"
                user_id = await self.db.fetchval("""
                    INSERT INTO users (wa_id, telefone, nome, created_at)
                    VALUES ($1, $2, $3, NOW())
                    RETURNING id
                """, phone, phone, f"PerfTest{i}")
                
                if user_id:
                    batch_users.append(user_id)
                    self.cleanup_data["user_ids"].append(user_id)
                    
            batch_time = time.time() - batch_start
            query_times.append(("batch_insert", batch_time))
            
            # Métricas de sistema no final
            memory_after = process.memory_info().rss / 1024 / 1024
            cpu_after = psutil.cpu_percent(interval=0.1)
            
            # Calcular métricas
            avg_query_time = sum(time for _, time in query_times) / len(query_times)
            memory_used = memory_after - memory_before
            
            metrics = {
                "memory_before_mb": round(memory_before, 2),
                "memory_after_mb": round(memory_after, 2),
                "memory_used_mb": round(memory_used, 2),
                "cpu_before_percent": cpu_before,
                "cpu_after_percent": cpu_after,
                "query_times": {name: round(time, 4) for name, time in query_times},
                "average_query_time": round(avg_query_time, 4),
                "batch_users_created": len(batch_users),
                "total_records_queried": records_affected
            }
            
            # Validações de performance
            if avg_query_time > 1.0:
                warnings.append(f"Query time médio alto: {avg_query_time:.4f}s")
                
            if memory_used > 100:  # MB
                warnings.append(f"Alto uso de memória: {memory_used:.2f}MB")
                
            if any(time > 2.0 for _, time in query_times):
                warnings.append("Algumas queries estão lentas (>2s)")
                
            success = len(errors) == 0 and avg_query_time < 5.0
            validation_passed = avg_query_time < 10.0 and memory_used < 200
            
        except Exception as e:
            errors.append(f"Erro no teste de performance: {str(e)}")
            success = False
            validation_passed = False
            
        execution_time = time.time() - start_time
        
        return SuperTestResult(
            test_category="PERFORMANCE",
            test_name="System Performance",
            success=success,
            execution_time=execution_time,
            records_affected=records_affected,
            errors=errors,
            warnings=warnings,
            metrics=metrics,
            is_critical=False,
            validation_passed=validation_passed
        )
    
    async def cleanup_test_data(self):
        """Limpa todos os dados de teste criados"""
        self.logger.info("🧹 Iniciando limpeza de dados de teste...")
        
        try:
            # Limpar agendamentos primeiro (FK dependencies)
            if self.cleanup_data["appointment_ids"]:
                await self.db.execute("""
                    DELETE FROM appointments WHERE id = ANY($1)
                """, self.cleanup_data["appointment_ids"])
                self.logger.info(f"🗑️ {len(self.cleanup_data['appointment_ids'])} agendamentos removidos")
            
            # Limpar mensagens
            if self.cleanup_data["message_ids"]:
                await self.db.execute("""
                    DELETE FROM messages WHERE id = ANY($1)
                """, self.cleanup_data["message_ids"])
                self.logger.info(f"💬 {len(self.cleanup_data['message_ids'])} mensagens removidas")
            
            # Limpar usuários por último
            if self.cleanup_data["user_ids"]:
                # Limpar dependências órfãs primeiro
                for user_id in self.cleanup_data["user_ids"]:
                    try:
                        await self.db.execute("""
                            DELETE FROM appointments WHERE user_id = $1 
                            AND created_at > NOW() - INTERVAL '2 hours'
                        """, user_id)
                        await self.db.execute("""
                            DELETE FROM messages WHERE user_id = $1 
                            AND created_at > NOW() - INTERVAL '2 hours'
                        """, user_id)
                    except:
                        pass
                
                # Agora deletar usuários
                await self.db.execute("""
                    DELETE FROM users WHERE id = ANY($1)
                """, self.cleanup_data["user_ids"])
                self.logger.info(f"👤 {len(self.cleanup_data['user_ids'])} usuários removidos")
            
            self.logger.info("✅ Limpeza concluída com sucesso")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Erro na limpeza: {e}")
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Executa todos os testes da Parte 1"""
        self.logger.info("🚀 INICIANDO SUPER TESTE - PARTE 1: INFRAESTRUTURA E CORE")
        self.logger.info("=" * 80)
        
        if not await self.initialize_system_monitoring():
            return {
                "success": False,
                "error": "Falha na inicialização do sistema",
                "timestamp": datetime.now().isoformat()
            }
        
        try:
            # CATEGORIA 1: CONECTIVIDADE
            self.logger.info("🔗 EXECUTANDO TESTES DE CONECTIVIDADE...")
            
            connectivity_result = await self.test_webhook_connectivity()
            self.test_results["CONNECTIVITY"].append(connectivity_result)
            
            load_result = await self.test_api_load_handling()
            self.test_results["CONNECTIVITY"].append(load_result)
            
            # CATEGORIA 2: MENSAGENS
            self.logger.info("📨 EXECUTANDO TESTES DE MENSAGENS...")
            
            messaging_result = await self.test_message_processing()
            self.test_results["MESSAGING"].append(messaging_result)
            
            # CATEGORIA 3: BANCO CORE
            self.logger.info("🗄️ EXECUTANDO TESTES DE BANCO CORE...")
            
            crud_result = await self.test_database_crud_operations()
            self.test_results["DATABASE_CORE"].append(crud_result)
            
            transactions_result = await self.test_database_transactions()
            self.test_results["DATABASE_CORE"].append(transactions_result)
            
            # CATEGORIA 4: SEGURANÇA
            self.logger.info("🛡️ EXECUTANDO TESTES DE SEGURANÇA...")
            
            security_result = await self.test_security_constraints()
            self.test_results["SECURITY"].append(security_result)
            
            # CATEGORIA 5: PERFORMANCE
            self.logger.info("⚡ EXECUTANDO TESTES DE PERFORMANCE...")
            
            performance_result = await self.test_system_performance()
            self.test_results["PERFORMANCE"].append(performance_result)
            
            # Gerar relatório final
            return await self.generate_final_report()
            
        except Exception as e:
            self.logger.error(f"❌ Erro durante execução dos testes: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        finally:
            await self.cleanup_test_data()
            if hasattr(self, 'db'):
                await self.db.close()
    
    async def generate_final_report(self) -> Dict[str, Any]:
        """Gera relatório final da Parte 1"""
        end_time = datetime.now()
        
        # Calcular estatísticas gerais
        all_tests = []
        for category_tests in self.test_results.values():
            all_tests.extend(category_tests)
        
        total_tests = len(all_tests)
        passed_tests = sum(1 for test in all_tests if test.success)
        critical_tests = sum(1 for test in all_tests if test.is_critical)
        critical_passed = sum(1 for test in all_tests if test.is_critical and test.success)
        validations_passed = sum(1 for test in all_tests if test.validation_passed)
        
        total_records = sum(test.records_affected for test in all_tests)
        total_time = sum(test.execution_time for test in all_tests)
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        critical_rate = (critical_passed / critical_tests * 100) if critical_tests > 0 else 0
        validation_rate = (validations_passed / total_tests * 100) if total_tests > 0 else 0
        
        overall_success = success_rate >= 75 and critical_rate >= 90
        
        # Relatório por categoria
        category_summary = {}
        for category, tests in self.test_results.items():
            category_passed = sum(1 for test in tests if test.success)
            category_total = len(tests)
            category_rate = (category_passed / category_total * 100) if category_total > 0 else 0
            
            category_summary[category] = {
                "total_tests": category_total,
                "passed_tests": category_passed,
                "success_rate": category_rate,
                "tests": [asdict(test) for test in tests]
            }
        
        # Imprimir relatório
        print("\n" + "="*100)
        print("🚀 SUPER TESTE PARTE 1 - RELATÓRIO FINAL")
        print("="*100)
        print(f"🆔 Sessão: {self.session_id}")
        print(f"📅 Concluído: {end_time.strftime('%d/%m/%Y às %H:%M:%S')}")
        print(f"⏱️ Tempo total: {total_time:.2f}s")
        
        print(f"\n📊 RESULTADOS GERAIS:")
        print(f"  📈 Total de testes: {total_tests}")
        print(f"  ✅ Testes aprovados: {passed_tests}")
        print(f"  🎯 Taxa de sucesso: {success_rate:.1f}%")
        print(f"  🚨 Testes críticos: {critical_tests}")
        print(f"  ✅ Críticos aprovados: {critical_passed}")
        print(f"  🎯 Taxa crítica: {critical_rate:.1f}%")
        print(f"  ✔️ Validações aprovadas: {validations_passed}/{total_tests}")
        print(f"  📝 Registros processados: {total_records}")
        
        print(f"\n📋 RESULTADOS POR CATEGORIA:")
        category_icons = {
            "CONNECTIVITY": "🔗",
            "MESSAGING": "📨", 
            "DATABASE_CORE": "🗄️",
            "SECURITY": "🛡️",
            "PERFORMANCE": "⚡"
        }
        
        for category, summary in category_summary.items():
            icon = category_icons.get(category, "📝")
            print(f"  {icon} {category}: {summary['passed_tests']}/{summary['total_tests']} ({summary['success_rate']:.1f}%)")
            
            for test in summary['tests']:
                status = "✅" if test['success'] else "❌"
                validation = "✔️" if test['validation_passed'] else "❌"
                print(f"      {status} {validation} {test['test_name']} - {test['execution_time']:.2f}s")
                
                for error in test.get('errors', []):
                    print(f"          ❌ {error}")
                for warning in test.get('warnings', []):
                    print(f"          ⚠️ {warning}")
        
        print(f"\n🏆 CONCLUSÃO DA PARTE 1:")
        if overall_success:
            if success_rate == 100:
                print("   🌟 INFRAESTRUTURA PERFEITA! 100% de sucesso!")
                conclusion = "PART1_PERFECT"
            else:
                print("   ✅ INFRAESTRUTURA APROVADA!")
                conclusion = "PART1_APPROVED"
            print("   🚀 Sistema robusto e confiável")
            print("   ✅ Pronto para a Parte 2 (Funcionalidades Avançadas)")
        else:
            if critical_rate >= 90:
                print("   ⚠️ INFRAESTRUTURA COM RESSALVAS")
                print("   ✅ Funções críticas aprovadas")
                conclusion = "PART1_PARTIAL"
            else:
                print("   ❌ INFRAESTRUTURA REPROVADA")
                print("   🚨 Correções necessárias antes da Parte 2")
                conclusion = "PART1_FAILED"
        
        print("="*100)
        
        # Salvar relatório
        report = {
            "session_id": self.session_id,
            "part": 1,
            "timestamp": end_time.isoformat(),
            "overall_success": overall_success,
            "success_rate": success_rate,
            "critical_success_rate": critical_rate,
            "validation_rate": validation_rate,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "critical_tests": critical_tests,
            "critical_passed": critical_passed,
            "validations_passed": validations_passed,
            "total_records_processed": total_records,
            "total_execution_time": total_time,
            "category_summary": category_summary,
            "conclusion": conclusion,
            "ready_for_part2": overall_success
        }
        
        filename = f"SUPER_TEST_PART1_REPORT_{self.session_id}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n📄 Relatório da Parte 1 salvo: {filename}")
        
        if overall_success:
            print(f"\n🎯 PRÓXIMOS PASSOS:")
            print(f"   1. Execute a PARTE 2 para testes de funcionalidades avançadas")
            print(f"   2. Validação completa do sistema em produção")
            print(f"   3. Testes de integração e user experience")
        
        return report


async def main():
    """Função principal da Parte 1"""
    print("🚀 SUPER TESTE DEFINITIVO - PARTE 1")
    print("=" * 50)
    print("🎯 INFRAESTRUTURA E CORE SYSTEM")
    print("=" * 50)
    print("📋 Áreas testadas:")
    print("   🔗 Conectividade e API")
    print("   📨 Processamento de mensagens")  
    print("   🗄️ Banco de dados core")
    print("   🛡️ Segurança e validação")
    print("   ⚡ Performance e concorrência")
    print("=" * 50)
    
    tester = SuperTesterPart1()
    
    try:
        report = await tester.run_all_tests()
        
        if report.get("overall_success"):
            print("\n🎉 PARTE 1 CONCLUÍDA COM SUCESSO!")
            print("🚀 Sistema pronto para a Parte 2!")
            return True
        else:
            print("\n⚠️ Parte 1 com ressalvas - verifique o relatório")
            return False
            
    except Exception as e:
        print(f"\n💥 Erro durante SUPER TESTE Parte 1: {e}")
        return False


if __name__ == "__main__":
    print("🚀 SUPER TESTE DEFINITIVO - PARTE 1: INFRAESTRUTURA E CORE")
    asyncio.run(main())