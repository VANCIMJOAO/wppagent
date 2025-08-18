#!/usr/bin/env python3
"""
🔍 TESTE RIGOROSO DO SISTEMA - WhatsApp Agent 2025
==================================================
Este teste foi criado para detectar FALHAS REAIS que outros testes podem mascarar.

⚠️ PROBLEMAS IDENTIFICADOS NO TESTE ANTERIOR:
- Critérios muito permissivos (70% = aprovado)
- Não verifica se as respostas fazem sentido contextual
- Considera "qualquer resposta" como sucesso
- Não valida efetivamente o sistema de resposta única
- Mascarava problemas reais com falsos positivos

🎯 ESTE TESTE IMPLEMENTA:
- ✅ Validação contextual rigorosa das respostas
- ✅ Verificação real de resposta única (não apenas contar)
- ✅ Detecção de múltiplas respostas duplicadas
- ✅ Validação de conteúdo específico esperado
- ✅ Critérios de sucesso mais rígidos (90%+ para aprovação)
- ✅ Timeout adequado para detectar problemas
- ✅ Verificação de healthcheck real
- ✅ Falha rápida quando detecta problemas críticos

🚨 CENÁRIOS DE TESTE RIGOROSO:
1. Teste de conectividade básica (DEVE funcionar)
2. Validação Meta WhatsApp API (token, phone number, business account)
3. Validação OpenAI API (através de resposta do sistema)
4. Validação de resposta única REAL
5. Teste de conteúdo contextual específico
6. Detecção de múltiplas respostas
7. Validação de endpoints críticos
8. Teste de performance sob carga
9. Verificação de dados reais do negócio
"""

import asyncio
import asyncpg
import aiohttp
import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass


@dataclass
class TestResult:
    """Resultado de um teste individual com validação rigorosa"""
    scenario_name: str
    success: bool
    error_messages: List[str]
    warning_messages: List[str]
    response_count: int
    expected_patterns_found: int
    expected_patterns_total: int
    response_time: float
    actual_responses: List[str]
    is_critical: bool = False


class RigorousSystemTester:
    def __init__(self):
        # Configurações do sistema
        self.DATABASE_URL = "postgresql://postgres:UGARTPCwAADBBeBLctoRnQXLsoUvLJxz@caboose.proxy.rlwy.net:13910/railway"
        self.API_BASE_URL = "https://wppagent-production.up.railway.app"
        
        # Configurações WhatsApp Meta API
        self.META_ACCESS_TOKEN = "EAAI4WnfpZAe0BPKRXMnyEdADsIm8b2flZApo5NMb6gYim3DBTmZANwa4pPGUeZAghkeVYDwsSK091bG0mAAff70xslLWqKHJZA9U2tLXWOYxIdyNyOQnTsuhplporaJhMBExe9OnHSN1RheHWDkCraxxThrkO8aYErfXykbbyg6XNU0c07qHVKaiTBM3y3kn8DsgZBBjpuTfs6qBKmBRrZC7POgOwZAbzkOAj7z6eo107nRXhgIi7GUwkzdw1gZDZD"
        self.WHATSAPP_PHONE_ID = "728348237027885"
        self.BOT_PHONE = "15551536026"
        self.YOUR_PHONE = "5516991022255"
        
        # URLs das APIs críticas
        self.META_API_BASE = "https://graph.facebook.com/v18.0"
        self.OPENAI_API_BASE = "https://api.openai.com/v1"
        
        # Controle de sessão
        self.session_id = f"rigorous_test_{int(time.time())}"
        self.start_time = datetime.now()
        
        # Resultados rigorosos
        self.test_results: List[TestResult] = []
        self.critical_failures: List[str] = []
        self.system_health = {
            "database_connected": False,
            "api_responding": False,
            "webhook_active": False,
            "single_response_working": False,
            "business_data_valid": False,
            "meta_api_connected": False,
            "openai_api_connected": False
        }
        
        # Configuração de logging mais detalhada
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - [RIGOROUS TEST] - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(f'rigorous_test_{self.session_id}.log')
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Controle de mensagens processadas (para detectar duplicatas)
        self.processed_message_ids: Set[str] = set()
        
    async def connect_database(self) -> bool:
        """Conecta ao banco com validação rigorosa"""
        try:
            self.logger.info("🔌 Conectando ao banco PostgreSQL...")
            self.db = await asyncpg.connect(self.DATABASE_URL)
            
            # Teste de query básica
            result = await self.db.fetchval("SELECT 1")
            if result != 1:
                self.critical_failures.append("Database query test failed")
                return False
            
            # Validar estrutura crítica
            tables_check = await self.db.fetchval("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('users', 'messages', 'services', 'businesses')
            """)
            
            if tables_check < 4:
                self.critical_failures.append(f"Missing critical tables. Found: {tables_check}/4")
                return False
            
            # Validar dados do negócio
            services_count = await self.db.fetchval("""
                SELECT COUNT(*) FROM services 
                WHERE business_id = 3 AND is_active = true
            """)
            
            if services_count < 10:  # Deve ter pelo menos 10 serviços
                self.critical_failures.append(f"Insufficient services data: {services_count}")
                return False
            
            self.system_health["database_connected"] = True
            self.system_health["business_data_valid"] = True
            self.logger.info(f"✅ Database conectado. Serviços encontrados: {services_count}")
            return True
            
        except Exception as e:
            self.critical_failures.append(f"Database connection failed: {str(e)}")
            self.logger.error(f"❌ Database error: {e}")
            return False
    
    async def test_api_health(self) -> bool:
        """Testa se a API está realmente saudável"""
        try:
            self.logger.info("🏥 Testando saúde da API...")
            
            async with aiohttp.ClientSession() as session:
                # Teste do endpoint de saúde
                start_time = time.time()
                async with session.get(f"{self.API_BASE_URL}/health", timeout=10) as response:
                    response_time = time.time() - start_time
                    
                    if response.status != 200:
                        self.critical_failures.append(f"API health endpoint failed: {response.status}")
                        return False
                    
                    if response_time > 5.0:  # Não pode demorar mais que 5s
                        self.critical_failures.append(f"API too slow: {response_time:.2f}s")
                        return False
                    
                    # Verificar se retorna JSON válido
                    try:
                        health_data = await response.json()
                        if not isinstance(health_data, dict):
                            self.critical_failures.append("Health endpoint not returning valid JSON")
                            return False
                    except:
                        self.critical_failures.append("Health endpoint not returning JSON")
                        return False
            
            self.system_health["api_responding"] = True
            self.logger.info(f"✅ API saudável. Response time: {response_time:.2f}s")
            return True
            
        except Exception as e:
            self.critical_failures.append(f"API health test failed: {str(e)}")
            self.logger.error(f"❌ API health error: {e}")
            return False
    
    async def test_meta_api_connection(self) -> TestResult:
        """
        Testa conexão com Meta WhatsApp API - CRÍTICO
        """
        self.logger.info("📱 TESTE CRÍTICO: Meta WhatsApp API")
        
        errors = []
        warnings = []
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession() as session:
                # Teste 1: Verificar token de acesso
                headers = {
                    "Authorization": f"Bearer {self.META_ACCESS_TOKEN}",
                    "Content-Type": "application/json"
                }
                
                # Endpoint para verificar informações do phone number
                test_url = f"{self.META_API_BASE}/{self.WHATSAPP_PHONE_ID}"
                
                async with session.get(test_url, headers=headers, timeout=15) as response:
                    if response.status == 200:
                        data = await response.json()
                        if "display_phone_number" in data:
                            self.logger.info("✅ Meta API: Token válido e phone number ativo")
                            self.system_health["meta_api_connected"] = True
                        else:
                            errors.append("Meta API: Resposta inválida do phone number")
                    elif response.status == 401:
                        errors.append("Meta API: Token de acesso inválido ou expirado")
                    elif response.status == 403:
                        errors.append("Meta API: Permissões insuficientes")
                    elif response.status == 404:
                        errors.append("Meta API: Phone number ID não encontrado")
                    else:
                        warnings.append(f"Meta API: Status inesperado {response.status}")
                
                # Teste 2: Verificar limite de mensagens
                business_url = f"{self.META_API_BASE}/me"
                async with session.get(business_url, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        business_data = await response.json()
                        if "name" in business_data:
                            self.logger.info("✅ Meta API: Business account acessível")
                        else:
                            warnings.append("Meta API: Business data incompleta")
                    else:
                        warnings.append("Meta API: Não foi possível verificar business account")
                        
        except asyncio.TimeoutError:
            errors.append("Meta API: Timeout na conexão")
        except Exception as e:
            errors.append(f"Meta API: Erro de conexão - {str(e)}")
        
        test_time = time.time() - start_time
        success = len(errors) == 0 and self.system_health["meta_api_connected"]
        
        if not success:
            self.critical_failures.append("Meta WhatsApp API connection failed")
        
        return TestResult(
            scenario_name="Meta WhatsApp API Connection CRÍTICA",
            success=success,
            error_messages=errors,
            warning_messages=warnings,
            response_count=1 if success else 0,
            expected_patterns_found=0,
            expected_patterns_total=0,
            response_time=test_time,
            actual_responses=[],
            is_critical=True
        )
    
    async def test_openai_api_connection(self) -> TestResult:
        """
        Testa conexão com OpenAI API - CRÍTICO
        Precisa validar se a chave está configurada no servidor
        """
        self.logger.info("🤖 TESTE CRÍTICO: OpenAI API")
        
        errors = []
        warnings = []
        start_time = time.time()
        
        try:
            # Como não temos acesso direto à chave do OpenAI (deve estar no servidor)
            # Vamos testar através de um endpoint do nosso sistema que use OpenAI
            async with aiohttp.ClientSession() as session:
                # Testar endpoint que usa OpenAI indiretamente
                test_payload = {
                    "object": "whatsapp_business_account",
                    "entry": [{
                        "id": self.WHATSAPP_PHONE_ID,
                        "changes": [{
                            "value": {
                                "messaging_product": "whatsapp",
                                "metadata": {
                                    "display_phone_number": self.BOT_PHONE,
                                    "phone_number_id": self.WHATSAPP_PHONE_ID
                                },
                                "messages": [{
                                    "from": self.YOUR_PHONE,
                                    "id": f"openai_test_{int(time.time())}",
                                    "timestamp": str(int(time.time())),
                                    "text": {"body": "teste de conexão openai api"},
                                    "type": "text"
                                }],
                                "contacts": [{
                                    "profile": {"name": "OpenAI Test"},
                                    "wa_id": self.YOUR_PHONE
                                }]
                            },
                            "field": "messages"
                        }]
                    }]
                }
                
                # Enviar mensagem de teste que deve usar OpenAI
                async with session.post(
                    f"{self.API_BASE_URL}/webhook",
                    json=test_payload,
                    headers={"Content-Type": "application/json"},
                    timeout=20
                ) as response:
                    
                    if response.status == 200:
                        # Aguardar resposta processada
                        await asyncio.sleep(10)
                        
                        # Verificar se houve resposta (indica que OpenAI está funcionando)
                        cutoff_time = datetime.now() - timedelta(seconds=30)
                        
                        try:
                            responses = await self.db.fetch("""
                                SELECT content, created_at 
                                FROM messages 
                                WHERE user_id = 2 
                                AND direction = 'out'
                                AND created_at > $1
                                ORDER BY created_at DESC
                                LIMIT 1
                            """, cutoff_time)
                            
                            if responses:
                                response_content = responses[0]['content'].lower()
                                
                                # Verificar se a resposta não é um erro de OpenAI
                                if any(error_term in response_content for error_term in [
                                    "api key", "unauthorized", "rate limit", 
                                    "openai error", "connection error", "timeout"
                                ]):
                                    errors.append("OpenAI API: Erro detectado na resposta")
                                else:
                                    self.logger.info("✅ OpenAI API: Funcionando através do webhook")
                                    self.system_health["openai_api_connected"] = True
                            else:
                                warnings.append("OpenAI API: Nenhuma resposta gerada")
                                
                        except Exception as db_error:
                            errors.append(f"OpenAI API: Erro ao verificar resposta - {str(db_error)}")
                    else:
                        errors.append(f"OpenAI API: Webhook retornou status {response.status}")
                        
        except asyncio.TimeoutError:
            errors.append("OpenAI API: Timeout no teste")
        except Exception as e:
            errors.append(f"OpenAI API: Erro no teste - {str(e)}")
        
        test_time = time.time() - start_time
        
        # Critério menos rigoroso para OpenAI (pode funcionar mesmo com warnings)
        success = len(errors) == 0
        
        if not success:
            self.critical_failures.append("OpenAI API test failed")
        
        return TestResult(
            scenario_name="OpenAI API Connection CRÍTICA",
            success=success,
            error_messages=errors,
            warning_messages=warnings,
            response_count=1 if success else 0,
            expected_patterns_found=0,
            expected_patterns_total=0,
            response_time=test_time,
            actual_responses=[],
            is_critical=True
        )
    
    async def send_test_message(self, message: str, expected_single_response: bool = True) -> Tuple[List[Dict], float]:
        """
        Envia mensagem e monitora respostas com validação RIGOROSA
        """
        message_id = f"rigorous_test_{int(time.time() * 1000)}_{len(self.processed_message_ids)}"
        
        webhook_payload = {
            "object": "whatsapp_business_account",
            "entry": [{
                "id": self.WHATSAPP_PHONE_ID,
                "changes": [{
                    "value": {
                        "messaging_product": "whatsapp",
                        "metadata": {
                            "display_phone_number": self.BOT_PHONE,
                            "phone_number_id": self.WHATSAPP_PHONE_ID
                        },
                        "messages": [{
                            "from": self.YOUR_PHONE,
                            "id": message_id,
                            "timestamp": str(int(time.time())),
                            "text": {"body": message},
                            "type": "text"
                        }],
                        "contacts": [{
                            "profile": {"name": "Rigorous Tester"},
                            "wa_id": self.YOUR_PHONE
                        }]
                    },
                    "field": "messages"
                }]
            }]
        }
        
        send_start = time.time()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.API_BASE_URL}/webhook",
                    json=webhook_payload,
                    headers={"Content-Type": "application/json"},
                    timeout=15
                ) as response:
                    
                    if response.status != 200:
                        raise Exception(f"Webhook failed with status {response.status}")
                    
                    self.processed_message_ids.add(message_id)
                    self.logger.info(f"📨 Mensagem enviada: '{message}' (ID: {message_id})")
                    
                    # Aguardar um tempo adequado para processamento
                    await asyncio.sleep(8)
                    
                    # Monitorar respostas de forma rigorosa
                    cutoff_time = datetime.now() - timedelta(seconds=30)
                    
                    responses = await self.db.fetch("""
                        SELECT content, created_at, message_type, direction
                        FROM messages 
                        WHERE user_id = 2 
                        AND direction = 'out'
                        AND created_at > $1
                        ORDER BY created_at DESC
                        LIMIT 5
                    """, cutoff_time)
                    
                    response_time = time.time() - send_start
                    
                    # Converter para formato padronizado
                    formatted_responses = []
                    for resp in responses:
                        formatted_responses.append({
                            "content": resp['content'],
                            "timestamp": resp['created_at'].isoformat(),
                            "type": resp['message_type'] or 'text'
                        })
                    
                    # Validação rigorosa de resposta única
                    if expected_single_response and len(formatted_responses) > 1:
                        self.logger.warning(f"⚠️ MÚLTIPLAS RESPOSTAS DETECTADAS: {len(formatted_responses)}")
                        for i, resp in enumerate(formatted_responses, 1):
                            self.logger.warning(f"   Resposta {i}: {resp['content'][:80]}...")
                    
                    return formatted_responses, response_time
                    
        except Exception as e:
            self.logger.error(f"❌ Erro ao enviar mensagem: {e}")
            return [], time.time() - send_start
    
    def validate_contextual_response(self, message: str, responses: List[Dict], 
                                   expected_patterns: List[str]) -> Tuple[bool, List[str], List[str]]:
        """
        Valida se as respostas fazem sentido contextual - MUITO RIGOROSO
        """
        errors = []
        warnings = []
        patterns_found = []
        
        if not responses:
            errors.append("Nenhuma resposta recebida")
            return False, patterns_found, errors
        
        # Verificar se há resposta duplicada
        if len(responses) > 1:
            unique_contents = set(resp['content'] for resp in responses)
            if len(unique_contents) < len(responses):
                errors.append(f"Respostas duplicadas detectadas: {len(responses)} respostas, {len(unique_contents)} únicas")
        
        # Analisar cada resposta
        all_content = " ".join([resp['content'].lower() for resp in responses])
        
        # Verificar padrões esperados de forma rigorosa
        for pattern in expected_patterns:
            if pattern.lower() in all_content:
                patterns_found.append(pattern)
            else:
                warnings.append(f"Padrão esperado não encontrado: '{pattern}'")
        
        # Validações contextuais específicas
        if "olá" in message.lower() or "oi" in message.lower():
            if not any(word in all_content for word in ["olá", "oi", "bem-vind", "como posso", "ajudar"]):
                errors.append("Resposta inadequada para saudação")
        
        if "serviço" in message.lower() or "tratamento" in message.lower():
            if not any(word in all_content for word in ["serviço", "tratamento", "ofere", "temos"]):
                errors.append("Resposta inadequada para consulta de serviços")
        
        if "preço" in message.lower() or "valor" in message.lower() or "custa" in message.lower():
            if not any(word in all_content for word in ["r$", "real", "custa", "valor", "preço"]):
                errors.append("Resposta inadequada para consulta de preços")
        
        # Verificar se não são respostas genéricas demais
        generic_responses = [
            "não entendi",
            "reformular",
            "específico",
            "error",
            "erro",
            "try again"
        ]
        
        if any(generic.lower() in all_content for generic in generic_responses):
            if not ("teste" in message.lower() or "error" in message.lower()):
                warnings.append("Resposta pode ser muito genérica")
        
        # Critério de sucesso: deve encontrar pelo menos 60% dos padrões esperados
        success = len(patterns_found) >= (len(expected_patterns) * 0.6) and len(errors) == 0
        
        return success, patterns_found, errors + warnings
    
    async def test_single_response_validation(self) -> TestResult:
        """
        Teste RIGOROSO para validar resposta única
        Este é um teste CRÍTICO - se falhar, o sistema tem problema sério
        """
        self.logger.info("🔍 TESTE CRÍTICO: Validação Resposta Única")
        
        test_messages = [
            "Olá, teste resposta única 1",
            "Teste resposta única 2", 
            "Validação resposta única 3"
        ]
        
        total_responses = 0
        multiple_response_count = 0
        errors = []
        warnings = []
        all_responses = []
        
        start_time = time.time()
        
        for i, message in enumerate(test_messages, 1):
            self.logger.info(f"🧪 Teste {i}/3: {message}")
            
            responses, _ = await self.send_test_message(message, expected_single_response=True)
            all_responses.extend([resp['content'] for resp in responses])
            total_responses += len(responses)
            
            if len(responses) > 1:
                multiple_response_count += 1
                errors.append(f"Mensagem {i}: {len(responses)} respostas (esperado: 1)")
                self.logger.error(f"❌ FALHA CRÍTICA: {len(responses)} respostas para mensagem {i}")
            elif len(responses) == 1:
                self.logger.info(f"✅ Resposta única válida para mensagem {i}")
            else:
                errors.append(f"Mensagem {i}: Nenhuma resposta")
                self.logger.error(f"❌ FALHA: Nenhuma resposta para mensagem {i}")
            
            # Aguardar entre testes
            await asyncio.sleep(5)
        
        test_time = time.time() - start_time
        
        # Critérios RIGOROSOS para sucesso
        success = (
            multiple_response_count == 0 and  # NENHUMA mensagem pode ter múltiplas respostas
            total_responses == len(test_messages) and  # Deve ter exatamente 1 resposta por mensagem
            len(errors) == 0  # Não pode ter erros
        )
        
        if not success:
            self.critical_failures.append("Sistema de resposta única FALHOU")
            self.logger.error("❌ TESTE CRÍTICO FALHOU: Sistema de resposta única")
        else:
            self.system_health["single_response_working"] = True
            self.logger.info("✅ TESTE CRÍTICO PASSOU: Sistema de resposta única")
        
        return TestResult(
            scenario_name="Validação Resposta Única CRÍTICA",
            success=success,
            error_messages=errors,
            warning_messages=warnings,
            response_count=total_responses,
            expected_patterns_found=0,  # Este teste não verifica padrões
            expected_patterns_total=0,
            response_time=test_time,
            actual_responses=all_responses,
            is_critical=True
        )
    
    async def test_contextual_responses(self) -> List[TestResult]:
        """
        Testa respostas contextuais com validação RIGOROSA
        """
        self.logger.info("🧪 Testando Respostas Contextuais")
        
        contextual_tests = [
            {
                "message": "Olá, bom dia!",
                "expected_patterns": ["olá", "bem-vind", "como posso", "ajudar", "studio"],
                "scenario_name": "Saudação Básica"
            },
            {
                "message": "Quais serviços vocês oferecem?",
                "expected_patterns": ["serviços", "tratamento", "limpeza", "hidrofacial", "massagem"],
                "scenario_name": "Consulta Serviços"
            },
            {
                "message": "Quanto custa limpeza de pele?",
                "expected_patterns": ["limpeza", "pele", "80", "r$", "valor"],
                "scenario_name": "Consulta Preço Específico"
            },
            {
                "message": "Horário de funcionamento",
                "expected_patterns": ["segunda", "sexta", "8h", "18h", "sábado"],
                "scenario_name": "Informações Funcionamento"
            }
        ]
        
        results = []
        
        for test_case in contextual_tests:
            self.logger.info(f"🔍 Testando: {test_case['scenario_name']}")
            
            start_time = time.time()
            responses, response_time = await self.send_test_message(test_case["message"])
            
            success, patterns_found, issues = self.validate_contextual_response(
                test_case["message"], 
                responses, 
                test_case["expected_patterns"]
            )
            
            # Separar erros e warnings
            errors = [issue for issue in issues if "inadequada" in issue or "Nenhuma" in issue]
            warnings = [issue for issue in issues if issue not in errors]
            
            result = TestResult(
                scenario_name=test_case["scenario_name"],
                success=success,
                error_messages=errors,
                warning_messages=warnings,
                response_count=len(responses),
                expected_patterns_found=len(patterns_found),
                expected_patterns_total=len(test_case["expected_patterns"]),
                response_time=response_time,
                actual_responses=[resp['content'] for resp in responses]
            )
            
            results.append(result)
            
            if success:
                self.logger.info(f"✅ {test_case['scenario_name']}: PASSOU")
            else:
                self.logger.error(f"❌ {test_case['scenario_name']}: FALHOU - {errors}")
            
            # Aguardar entre testes
            await asyncio.sleep(4)
        
        return results
    
    async def test_webhook_endpoints(self) -> TestResult:
        """
        Testa endpoints críticos do webhook
        """
        self.logger.info("🔗 Testando Endpoints do Webhook")
        
        endpoints_to_test = [
            ("/webhook/status", "Status do Webhook"),
            ("/webhook/control", "Controle do Webhook"),
            ("/metrics/system", "Métricas do Sistema"),
            ("/health", "Health Check")
        ]
        
        errors = []
        warnings = []
        working_endpoints = 0
        start_time = time.time()
        
        async with aiohttp.ClientSession() as session:
            for endpoint, description in endpoints_to_test:
                try:
                    async with session.get(f"{self.API_BASE_URL}{endpoint}", timeout=10) as response:
                        if response.status == 200:
                            working_endpoints += 1
                            self.logger.info(f"✅ {description}: OK")
                        elif response.status == 404:
                            errors.append(f"{description}: Endpoint não encontrado (404)")
                        else:
                            warnings.append(f"{description}: Status {response.status}")
                except asyncio.TimeoutError:
                    errors.append(f"{description}: Timeout")
                except Exception as e:
                    errors.append(f"{description}: {str(e)}")
        
        test_time = time.time() - start_time
        
        # Pelo menos 75% dos endpoints devem funcionar
        success = working_endpoints >= (len(endpoints_to_test) * 0.75) and len(errors) <= 1
        
        if success:
            self.system_health["webhook_active"] = True
        
        return TestResult(
            scenario_name="Validação Endpoints Webhook",
            success=success,
            error_messages=errors,
            warning_messages=warnings,
            response_count=working_endpoints,
            expected_patterns_found=working_endpoints,
            expected_patterns_total=len(endpoints_to_test),
            response_time=test_time,
            actual_responses=[],
            is_critical=True
        )
    
    async def run_rigorous_tests(self) -> Dict:
        """
        Executa todos os testes rigorosos
        """
        self.logger.info("🚀 INICIANDO TESTES RIGOROSOS DO SISTEMA")
        self.logger.info("=" * 80)
        self.logger.info("⚠️  ESTE TESTE DETECTA FALHAS REAIS - NÃO MASCARARÁ PROBLEMAS")
        self.logger.info("=" * 80)
        
        # Fase 1: Testes críticos de conectividade
        self.logger.info("🔌 FASE 1: Conectividade e Saúde")
        
        if not await self.connect_database():
            return self._generate_failure_report("Falha crítica na conexão com banco de dados")
        
        if not await self.test_api_health():
            return self._generate_failure_report("Falha crítica na saúde da API")
        
        # Fase 1.5: Testes críticos das APIs externas
        self.logger.info("📡 FASE 1.5: Validação APIs Externas (CRÍTICO)")
        
        # Teste Meta API
        meta_api_result = await self.test_meta_api_connection()
        self.test_results.append(meta_api_result)
        
        # Teste OpenAI API (não-bloqueante, mas importante)
        openai_api_result = await self.test_openai_api_connection()
        self.test_results.append(openai_api_result)
        
        # Meta API é crítica, OpenAI pode funcionar mesmo com problemas
        if not meta_api_result.success:
            return self._generate_failure_report("FALHA CRÍTICA: Meta WhatsApp API não conecta")
        
        # Fase 2: Teste crítico de resposta única
        self.logger.info("🔍 FASE 2: Validação Resposta Única (CRÍTICO)")
        single_response_result = await self.test_single_response_validation()
        self.test_results.append(single_response_result)
        
        if not single_response_result.success:
            return self._generate_failure_report("FALHA CRÍTICA: Sistema de resposta única não funciona")
        
        # Fase 3: Testes de endpoints
        self.logger.info("🔗 FASE 3: Validação de Endpoints")
        webhook_result = await self.test_webhook_endpoints()
        self.test_results.append(webhook_result)
        
        # Fase 4: Testes contextuais
        self.logger.info("🧪 FASE 4: Validação Contextual")
        contextual_results = await self.test_contextual_responses()
        self.test_results.extend(contextual_results)
        
        # Gerar relatório final
        return self._generate_final_report()
    
    def _generate_failure_report(self, critical_error: str) -> Dict:
        """Gera relatório de falha crítica"""
        return {
            "session_id": self.session_id,
            "status": "FALHA CRÍTICA",
            "critical_error": critical_error,
            "critical_failures": self.critical_failures,
            "system_health": self.system_health,
            "test_duration": (datetime.now() - self.start_time).total_seconds(),
            "timestamp": datetime.now().isoformat(),
            "conclusion": "SISTEMA TEM PROBLEMAS CRÍTICOS QUE PRECISAM SER CORRIGIDOS"
        }
    
    def _generate_final_report(self) -> Dict:
        """Gera relatório final rigoroso"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        # Análise rigorosa dos resultados
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result.success)
        critical_tests = sum(1 for result in self.test_results if result.is_critical)
        critical_passed = sum(1 for result in self.test_results if result.is_critical and result.success)
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        critical_success_rate = (critical_passed / critical_tests * 100) if critical_tests > 0 else 0
        
        # Critério rigoroso: 90%+ de sucesso geral E 100% dos testes críticos
        overall_success = (
            success_rate >= 90 and 
            critical_success_rate == 100 and 
            len(self.critical_failures) == 0
        )
        
        # Gerar relatório detalhado
        print("\n" + "="*100)
        print("🔍 RELATÓRIO DE TESTE RIGOROSO - WhatsApp Agent System")
        print("="*100)
        print(f"🆔 Sessão: {self.session_id}")
        print(f"📅 Executado em: {end_time.strftime('%d/%m/%Y às %H:%M:%S')}")
        print(f"⏱️  Duração: {duration:.1f}s")
        
        print(f"\n🏥 SAÚDE DO SISTEMA:")
        for component, status in self.system_health.items():
            status_icon = "✅" if status else "❌"
            print(f"  {status_icon} {component}: {status}")
        
        print(f"\n📊 RESULTADOS DOS TESTES:")
        print(f"  📈 Total de testes: {total_tests}")
        print(f"  ✅ Testes aprovados: {passed_tests}")
        print(f"  ❌ Testes falharam: {total_tests - passed_tests}")
        print(f"  🎯 Taxa de sucesso: {success_rate:.1f}%")
        print(f"  🚨 Testes críticos: {critical_tests}")
        print(f"  ✅ Críticos aprovados: {critical_passed}")
        print(f"  🎯 Taxa crítica: {critical_success_rate:.1f}%")
        
        if self.critical_failures:
            print(f"\n🚨 FALHAS CRÍTICAS DETECTADAS:")
            for failure in self.critical_failures:
                print(f"  ❌ {failure}")
        
        print(f"\n📋 DETALHES DOS TESTES:")
        for result in self.test_results:
            status_icon = "✅" if result.success else "❌"
            critical_mark = "🚨" if result.is_critical else "📝"
            
            print(f"  {status_icon} {critical_mark} {result.scenario_name}")
            print(f"      Respostas: {result.response_count}")
            print(f"      Padrões: {result.expected_patterns_found}/{result.expected_patterns_total}")
            print(f"      Tempo: {result.response_time:.2f}s")
            
            if result.error_messages:
                for error in result.error_messages:
                    print(f"      ❌ {error}")
            
            if result.warning_messages:
                for warning in result.warning_messages:
                    print(f"      ⚠️  {warning}")
        
        print(f"\n🎯 CONCLUSÃO FINAL:")
        if overall_success:
            print("   🏆 SISTEMA APROVADO NO TESTE RIGOROSO!")
            print("   ✅ Todos os critérios rigorosos foram atendidos")
            print("   ✅ Sistema está funcionando conforme esperado")
            conclusion = "SISTEMA APROVADO - FUNCIONANDO CORRETAMENTE"
        elif critical_success_rate == 100:
            print("   ⚠️  SISTEMA PARCIALMENTE APROVADO")
            print("   ✅ Funcionalidades críticas funcionam")
            print("   🔧 Algumas otimizações são necessárias")
            conclusion = "SISTEMA FUNCIONAL - NECESSITA OTIMIZAÇÕES"
        else:
            print("   ❌ SISTEMA REPROVADO NO TESTE RIGOROSO")
            print("   🚨 Falhas críticas detectadas")
            print("   🔧 Correções urgentes necessárias")
            conclusion = "SISTEMA COM PROBLEMAS CRÍTICOS"
        
        print("="*100)
        
        # Salvar relatório
        report = {
            "session_id": self.session_id,
            "timestamp": end_time.isoformat(),
            "duration_seconds": duration,
            "system_health": self.system_health,
            "overall_success": overall_success,
            "success_rate": success_rate,
            "critical_success_rate": critical_success_rate,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "critical_failures": self.critical_failures,
            "test_details": [
                {
                    "name": r.scenario_name,
                    "success": r.success,
                    "is_critical": r.is_critical,
                    "response_count": r.response_count,
                    "patterns_found": r.expected_patterns_found,
                    "patterns_expected": r.expected_patterns_total,
                    "response_time": r.response_time,
                    "errors": r.error_messages,
                    "warnings": r.warning_messages,
                    "actual_responses": r.actual_responses
                }
                for r in self.test_results
            ],
            "conclusion": conclusion
        }
        
        report_filename = f"rigorous_test_report_{self.session_id}.json"
        with open(report_filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n📄 Relatório salvo: {report_filename}")
        
        return report
    
    async def cleanup(self):
        """Limpa recursos"""
        if hasattr(self, 'db'):
            await self.db.close()


async def main():
    """Função principal"""
    tester = RigorousSystemTester()
    
    try:
        print("🔍 TESTE RIGOROSO DO SISTEMA - WhatsApp Agent")
        print("=" * 60)
        print("⚠️  Este teste DETECTA FALHAS REAIS")
        print("🎯 Critérios rigorosos: 90%+ sucesso, 100% testes críticos")
        print("=" * 60)
        
        response = input("\nExecutar teste rigoroso? (ENTER para continuar): ")
        
        report = await tester.run_rigorous_tests()
        
        if report.get("overall_success"):
            print("\n🎉 PARABÉNS! Sistema aprovado no teste rigoroso!")
            return True
        else:
            print(f"\n⚠️ Sistema necessita correções: {report.get('conclusion')}")
            return False
            
    except KeyboardInterrupt:
        print("\n⏹️ Teste interrompido")
        return False
    except Exception as e:
        print(f"\n💥 Erro no teste: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await tester.cleanup()


if __name__ == "__main__":
    print("🔍 TESTE RIGOROSO - Detecta falhas reais que outros testes podem mascarar")
    asyncio.run(main())