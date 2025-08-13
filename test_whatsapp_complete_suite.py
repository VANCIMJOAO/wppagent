#!/usr/bin/env python3
"""
🧪 SCRIPT COMPLETO DE TESTE - WhatsApp Agent
===========================================
Teste abrangente com todos os cenários e análise detalhada
"""

import asyncio
import aiohttp
import asyncpg
import json
import time
import random
import logging
import hmac
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Configurações
RAILWAY_URL = "https://wppagent-production.up.railway.app"
TEST_PHONE = "5516991022255"
WEBHOOK_URL = f"{RAILWAY_URL}/webhook"
DATABASE_URL = 'postgresql://postgres:UGARTPCwAADBBeBLctoRnQXLsoUvLJxz@caboose.proxy.rlwy.net:13910/railway'

# Setup logging
log_filename = f"whatsapp_test_complete_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class WhatsAppTester:
    def __init__(self):
        self.session = None
        self.db_conn = None
        self.test_results = []
        self.llm_responses = []
        self.start_time = datetime.now()
        self.debug_info = {}
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
        if self.db_conn:
            await self.db_conn.close()

    async def debug_system_check(self):
        """Verificações de debug antes dos testes"""
        logger.info("🔍 INICIANDO VERIFICAÇÕES DE DEBUG")
        logger.info("=" * 50)
        
        # Check 1: Health do sistema
        try:
            async with self.session.get(f"{RAILWAY_URL}/health") as response:
                health_data = await response.json()
                self.debug_info['health_check'] = {
                    "status": response.status,
                    "data": health_data,
                    "timestamp": datetime.now().isoformat()
                }
                logger.info(f"✅ Health Check: {response.status} - {health_data.get('status', 'unknown')}")
        except Exception as e:
            logger.error(f"❌ Health Check falhou: {e}")
            self.debug_info['health_check'] = {"error": str(e)}
        
        # Check 2: Health detalhado
        try:
            async with self.session.get(f"{RAILWAY_URL}/health/detailed") as response:
                detailed_health = await response.json()
                self.debug_info['detailed_health'] = {
                    "status": response.status,
                    "data": detailed_health,
                    "timestamp": datetime.now().isoformat()
                }
                logger.info(f"✅ Health Detalhado: {response.status}")
                if detailed_health.get('checks'):
                    for check_name, check_data in detailed_health['checks'].items():
                        logger.debug(f"   {check_name}: {check_data.get('status', 'unknown')}")
        except Exception as e:
            logger.error(f"❌ Health Detalhado falhou: {e}")
            self.debug_info['detailed_health'] = {"error": str(e)}
        
        # Check 3: Webhook status
        try:
            async with self.session.get(f"{RAILWAY_URL}/webhook/status") as response:
                webhook_status = await response.json()
                self.debug_info['webhook_status'] = {
                    "status": response.status,
                    "data": webhook_status,
                    "timestamp": datetime.now().isoformat()
                }
                logger.info(f"✅ Webhook Status: {response.status}")
                logger.debug(f"   Meta API: {webhook_status.get('meta_api', {}).get('status', 'unknown')}")
        except Exception as e:
            logger.error(f"❌ Webhook Status falhou: {e}")
            self.debug_info['webhook_status'] = {"error": str(e)}
        
        # Check 4: Conectividade do banco
        try:
            self.db_conn = await asyncpg.connect(DATABASE_URL)
            await self.db_conn.fetchval("SELECT 1")
            self.debug_info['database_check'] = {
                "status": "connected",
                "timestamp": datetime.now().isoformat()
            }
            logger.info("✅ Banco de dados conectado")
        except Exception as e:
            logger.error(f"❌ Conexão com banco falhou: {e}")
            self.debug_info['database_check'] = {"error": str(e)}
        
        # Check 5: Verificar se usuário existe
        if self.db_conn:
            try:
                user = await self.db_conn.fetchrow(
                    "SELECT id, wa_id, nome, created_at FROM users WHERE wa_id = $1 OR telefone = $1", 
                    TEST_PHONE
                )
                if user:
                    self.debug_info['user_check'] = {
                        "exists": True,
                        "user_id": user['id'],
                        "name": user['nome'],
                        "created": user['created_at'].isoformat()
                    }
                    logger.info(f"✅ Usuário encontrado: {user['nome']} (ID: {user['id']})")
                else:
                    self.debug_info['user_check'] = {"exists": False}
                    logger.info("ℹ️ Usuário não existe - será criado durante o teste")
            except Exception as e:
                logger.error(f"❌ Verificação de usuário falhou: {e}")
                self.debug_info['user_check'] = {"error": str(e)}
        
        # Check 6: Rate limit status
        try:
            async with self.session.get(f"{RAILWAY_URL}/rate-limit/stats") as response:
                rate_limit_stats = await response.json()
                self.debug_info['rate_limit_check'] = {
                    "status": response.status,
                    "data": rate_limit_stats,
                    "timestamp": datetime.now().isoformat()
                }
                logger.info(f"✅ Rate Limit Stats: {response.status}")
        except Exception as e:
            logger.warning(f"⚠️ Rate Limit Stats não disponível: {e}")
            self.debug_info['rate_limit_check'] = {"error": str(e)}
        
        logger.info("🔍 Verificações de debug concluídas")
        logger.info("=" * 50)
        
        return self.debug_info

    async def send_webhook_message(self, message: str, scenario: str, delay: float = 3.0):
        """Envia mensagem via webhook simulando WhatsApp"""
        message_id = f"wamid.test_{int(time.time())}{random.randint(1000, 9999)}"
        timestamp = str(int(time.time()))
        
        payload = {
            "object": "whatsapp_business_account",
            "entry": [{
                "id": "24386792860950513",
                "changes": [{
                    "value": {
                        "messaging_product": "whatsapp",
                        "metadata": {
                            "display_phone_number": "15550987654",
                            "phone_number_id": "728348237027885"
                        },
                        "contacts": [{
                            "profile": {
                                "name": "João Testador Sistema"
                            },
                            "wa_id": TEST_PHONE
                        }],
                        "messages": [{
                            "from": TEST_PHONE,
                            "id": message_id,
                            "timestamp": timestamp,
                            "type": "text",
                            "text": {
                                "body": message
                            }
                        }]
                    },
                    "field": "messages"
                }]
            }]
        }
        
        # Criar assinatura correta para o webhook
        payload_bytes = json.dumps(payload, separators=(',', ':')).encode()
        webhook_secret = "meutoken123"
        signature = hmac.new(webhook_secret.encode(), payload_bytes, hashlib.sha256).hexdigest()
        
        logger.info(f"📤 [{scenario}] Enviando: {message}")
        
        try:
            start_time = time.time()
            async with self.session.post(
                WEBHOOK_URL,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "WhatsApp/2.0",
                    "X-Hub-Signature-256": f"sha256={signature}"
                }
            ) as response:
                response_time = time.time() - start_time
                response_text = await response.text()
                
                result = {
                    "scenario": scenario,
                    "message": message,
                    "message_id": message_id,
                    "timestamp": datetime.now().isoformat(),
                    "status_code": response.status,
                    "response_time_ms": round(response_time * 1000, 2),
                    "response_body": response_text,
                    "webhook_payload": payload
                }
                
                self.test_results.append(result)
                
                logger.info(f"📨 [{scenario}] Status: {response.status} | Tempo: {result['response_time_ms']}ms")
                
                # Aguardar processamento e possível resposta
                await asyncio.sleep(delay)
                
                # Capturar resposta da LLM do banco
                await self.capture_llm_response(message, scenario)
                
                return result
                
        except Exception as e:
            logger.error(f"❌ [{scenario}] Erro ao enviar '{message}': {e}")
            error_result = {
                "scenario": scenario,
                "message": message,
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "status_code": 500
            }
            self.test_results.append(error_result)
            return error_result

    async def capture_llm_response(self, sent_message: str, scenario: str):
        """Captura resposta da LLM do banco de dados"""
        if not self.db_conn:
            return
        
        try:
            # Buscar mensagens mais recentes do sistema
            messages = await self.db_conn.fetch("""
                SELECT m.id, m.direction, m.content, m.created_at,
                       u.wa_id, u.nome
                FROM messages m
                JOIN users u ON m.user_id = u.id
                WHERE u.wa_id = $1 AND m.direction = 'out'
                ORDER BY m.created_at DESC
                LIMIT 3
            """, TEST_PHONE)
            
            for msg in messages:
                # Verificar se é uma resposta recente (últimos 10 segundos)
                time_diff = datetime.now() - msg['created_at']
                if time_diff.total_seconds() <= 10:
                    
                    llm_response = {
                        "scenario": scenario,
                        "user_message": sent_message,
                        "llm_response": msg['content'],
                        "message_id": msg['id'],
                        "timestamp": msg['created_at'].isoformat(),
                        "processing_system": "whatsapp_agent",
                        "confidence": 1.0,
                        "processing_time": time_diff.total_seconds()
                    }
                    
                    self.llm_responses.append(llm_response)
                    logger.debug(f"🤖 [{scenario}] LLM Response capturada: {msg['content'][:100]}...")
                    break
                    
        except Exception as e:
            logger.error(f"❌ Erro ao capturar resposta LLM: {e}")

    async def test_greeting_flow(self):
        """Cenário 1: Fluxo de saudação e apresentação"""
        logger.info("\n🎬 CENÁRIO 1: Saudação e Apresentação")
        
        messages = [
            "Olá!",
            "Bom dia! Como está?",
            "Gostaria de conhecer seus serviços",
            "Vocês trabalham com o quê?",
            "Que legal! Me conte mais"
        ]
        
        for msg in messages:
            await self.send_webhook_message(msg, "greeting", delay=2.5)

    async def test_service_inquiry_flow(self):
        """Cenário 2: Consulta detalhada de serviços"""
        logger.info("\n🎬 CENÁRIO 2: Consulta de Serviços")
        
        messages = [
            "Quais serviços vocês oferecem?",
            "Quanto custa uma limpeza de pele?",
            "E massagem relaxante, fazem?",
            "Qual a duração da limpeza de pele?",
            "Vocês fazem depilação também?",
            "Têm algum pacote promocional?",
            "E desconto para primeira vez?"
        ]
        
        for msg in messages:
            await self.send_webhook_message(msg, "service_inquiry", delay=3.0)

    async def test_appointment_booking_flow(self):
        """Cenário 3: Agendamento completo"""
        logger.info("\n🎬 CENÁRIO 3: Agendamento Completo")
        
        messages = [
            "Quero agendar um horário",
            "Limpeza de pele profunda",
            "Para quando vocês têm disponibilidade?",
            "Amanhã de manhã seria possível?",
            "Às 10h da manhã está bom?",
            "Perfeito! Meu nome é João Silva",
            "Meu telefone é 16 99102-2255",
            "Sim, confirmo o agendamento",
            "Obrigado!"
        ]
        
        for msg in messages:
            await self.send_webhook_message(msg, "appointment_booking", delay=3.5)

    async def test_cancellation_flow(self):
        """Cenário 4: Cancelamento de agendamento"""
        logger.info("\n🎬 CENÁRIO 4: Cancelamento")
        
        messages = [
            "Oi, preciso cancelar meu agendamento",
            "É o agendamento de amanhã às 10h",
            "Surgiu um imprevisto no trabalho",
            "Não consigo ir mesmo",
            "Sim, confirmo o cancelamento",
            "Desculpa pelo transtorno"
        ]
        
        for msg in messages:
            await self.send_webhook_message(msg, "cancellation", delay=2.5)

    async def test_reschedule_flow(self):
        """Cenário 5: Reagendamento"""
        logger.info("\n🎬 CENÁRIO 5: Reagendamento")
        
        messages = [
            "Na verdade, posso reagendar?",
            "Prefiro não cancelar completamente",
            "Que tal na sexta-feira?",
            "De tarde seria melhor",
            "Às 14h está disponível?",
            "Perfeito! Confirmo o reagendamento",
            "Sexta às 14h então"
        ]
        
        for msg in messages:
            await self.send_webhook_message(msg, "reschedule", delay=3.0)

    async def test_complaint_flow(self):
        """Cenário 6: Reclamação e resolução"""
        logger.info("\n🎬 CENÁRIO 6: Reclamação")
        
        messages = [
            "Estou insatisfeito com o atendimento",
            "A profissional chegou 30 minutos atrasada",
            "E o tratamento não foi como esperado",
            "Minha pele ficou irritada depois",
            "Gostaria de uma solução para isso",
            "Que tipo de compensação vocês oferecem?",
            "Sim, aceito um desconto no próximo",
            "Obrigado pela compreensão"
        ]
        
        for msg in messages:
            await self.send_webhook_message(msg, "complaint", delay=3.0)

    async def test_complex_inquiry_flow(self):
        """Cenário 7: Consulta complexa múltipla"""
        logger.info("\n🎬 CENÁRIO 7: Consulta Complexa")
        
        messages = [
            "Estou organizando um evento para minha empresa",
            "Precisamos de serviços para 10 pessoas",
            "Seria um day spa corporativo",
            "Quais pacotes vocês recomendam?",
            "Vocês fazem desconto para grupos?",
            "E se for num sábado, funciona?",
            "Precisaria ser em dezembro",
            "Quanto ficaria o orçamento total?"
        ]
        
        for msg in messages:
            await self.send_webhook_message(msg, "complex_inquiry", delay=3.5)

    async def test_business_info_flow(self):
        """Cenário 8: Informações do negócio"""
        logger.info("\n🎬 CENÁRIO 8: Informações do Negócio")
        
        messages = [
            "Vocês funcionam aos sábados?",
            "E domingo?",
            "Qual o horário de funcionamento?",
            "Onde vocês ficam localizados?",
            "Tem estacionamento?",
            "Como chegar de ônibus?",
            "Vocês têm Instagram?",
            "Aceitam cartão?"
        ]
        
        for msg in messages:
            await self.send_webhook_message(msg, "business_info", delay=2.0)

    async def test_multi_topic_flow(self):
        """Cenário 9: Conversa com múltiplos tópicos (fluxo não-linear)"""
        logger.info("\n🎬 CENÁRIO 9: Múltiplos Tópicos")
        
        messages = [
            "Oi! Queria saber sobre massagem",
            "Mas antes, vocês fazem sobrancelha?",
            "E unhas também?",
            "Voltando à massagem, qual o preço?",
            "É relaxante ou tem outras?",
            "Ah, e sobre a sobrancelha...",
            "Vocês fazem design?",
            "Ok, mas a massagem é hoje mesmo?",
            "Prefiro agendar a sobrancelha então",
            "Para amanhã de manhã"
        ]
        
        for msg in messages:
            await self.send_webhook_message(msg, "multi_topic", delay=2.5)

    async def test_edge_cases_flow(self):
        """Cenário 10: Casos extremos e edge cases"""
        logger.info("\n🎬 CENÁRIO 10: Casos Extremos")
        
        messages = [
            "asdfghjkl",  # Texto aleatório
            "😀😃😄😁😆😅😂🤣",  # Apenas emojis
            "QUERO AGENDAR AGORA!!!!!",  # Maiúsculas + urgência
            "vocês fazem botox? preenchimento? harmonização?",  # Serviços não oferecidos
            "123456789",  # Apenas números
            ".",  # Apenas ponto
            "oi" * 100,  # Texto repetitivo
            "Quanto custa? E quando? E onde? E como?",  # Múltiplas perguntas
            "CANCELAR TUDO!!!!!",  # Urgência em maiúsculas
            "Obrigado pela paciência, até logo!"  # Despedida educada
        ]
        
        for msg in messages:
            await self.send_webhook_message(msg, "edge_cases", delay=2.0)

    async def collect_final_metrics(self):
        """Coleta métricas finais do sistema e banco"""
        logger.info("\n📊 COLETANDO MÉTRICAS FINAIS")
        
        metrics = {}
        
        # Métricas da API
        endpoints = [
            ("/metrics/system", "system_metrics"),
            ("/conversation/analytics", "conversation_analytics"),
            ("/llm/analytics", "llm_analytics"),
            ("/alerts", "alerts"),
            (f"/conversation/flow/{TEST_PHONE}", "user_flow")
        ]
        
        for endpoint, key in endpoints:
            try:
                async with self.session.get(f"{RAILWAY_URL}{endpoint}") as response:
                    if response.status == 200:
                        data = await response.json()
                        metrics[key] = data
                        logger.debug(f"✅ {key}: coletado")
                    else:
                        logger.warning(f"⚠️ {key}: status {response.status}")
            except Exception as e:
                logger.error(f"❌ Erro ao coletar {key}: {e}")
        
        # Métricas do banco
        if self.db_conn:
            try:
                # Estatísticas gerais
                db_stats = {}
                tables = ['users', 'messages', 'conversations', 'appointments', 'services']
                
                for table in tables:
                    count = await self.db_conn.fetchval(f"SELECT COUNT(*) FROM {table}")
                    db_stats[table] = count
                
                # Dados específicos do usuário teste
                user_data = await self.db_conn.fetchrow("""
                    SELECT u.id, u.wa_id, u.nome, u.created_at,
                           COUNT(m.id) as total_messages,
                           COUNT(CASE WHEN m.direction = 'in' THEN 1 END) as incoming,
                           COUNT(CASE WHEN m.direction = 'out' THEN 1 END) as outgoing
                    FROM users u
                    LEFT JOIN messages m ON u.id = m.user_id
                    WHERE u.wa_id = $1
                    GROUP BY u.id, u.wa_id, u.nome, u.created_at
                """, TEST_PHONE)
                
                # Agendamentos do usuário
                appointments = await self.db_conn.fetch("""
                    SELECT a.*, s.name as service_name, s.price
                    FROM appointments a
                    LEFT JOIN users u ON a.user_id = u.id
                    LEFT JOIN services s ON a.service_id = s.id
                    WHERE u.wa_id = $1
                    ORDER BY a.created_at DESC
                """, TEST_PHONE)
                
                metrics['database'] = {
                    "tables_count": db_stats,
                    "test_user": dict(user_data) if user_data else None,
                    "user_appointments": [dict(apt) for apt in appointments]
                }
                
                logger.info(f"📊 Banco: {sum(db_stats.values())} registros totais")
                
            except Exception as e:
                logger.error(f"❌ Erro ao coletar métricas do banco: {e}")
        
        return metrics

    async def generate_comprehensive_report(self, final_metrics):
        """Gera relatório abrangente"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Calcular estatísticas
        total_messages = len(self.test_results)
        successful_messages = len([r for r in self.test_results if r.get('status_code') == 200])
        failed_messages = total_messages - successful_messages
        success_rate = (successful_messages / total_messages * 100) if total_messages > 0 else 0
        
        # Agrupar por cenário
        scenarios_stats = {}
        for result in self.test_results:
            scenario = result.get('scenario', 'unknown')
            if scenario not in scenarios_stats:
                scenarios_stats[scenario] = {'total': 0, 'success': 0, 'failed': 0}
            
            scenarios_stats[scenario]['total'] += 1
            if result.get('status_code') == 200:
                scenarios_stats[scenario]['success'] += 1
            else:
                scenarios_stats[scenario]['failed'] += 1
        
        # Relatório completo
        report = {
            "test_summary": {
                "start_time": self.start_time.isoformat(),
                "end_time": datetime.now().isoformat(),
                "duration_seconds": (datetime.now() - self.start_time).total_seconds(),
                "test_phone": TEST_PHONE,
                "railway_url": RAILWAY_URL,
                "total_messages": total_messages,
                "successful_messages": successful_messages,
                "failed_messages": failed_messages,
                "success_rate_percent": round(success_rate, 2),
                "total_llm_responses": len(self.llm_responses),
                "scenarios_tested": len(scenarios_stats)
            },
            "debug_info": self.debug_info,
            "scenarios_breakdown": scenarios_stats,
            "detailed_results": self.test_results,
            "llm_responses_captured": self.llm_responses,
            "system_metrics": final_metrics
        }
        
        # Salvar JSON detalhado
        json_filename = f"whatsapp_test_complete_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        # Relatório legível
        txt_filename = f"whatsapp_test_report_{timestamp}.txt"
        with open(txt_filename, 'w', encoding='utf-8') as f:
            f.write("🧪 RELATÓRIO COMPLETO DE TESTE - WHATSAPP AGENT\n")
            f.write("=" * 55 + "\n\n")
            
            # Resumo
            f.write("📊 RESUMO EXECUTIVO\n")
            f.write("-" * 20 + "\n")
            f.write(f"Duração: {report['test_summary']['duration_seconds']:.1f}s\n")
            f.write(f"Mensagens enviadas: {total_messages}\n")
            f.write(f"Taxa de sucesso: {success_rate:.1f}%\n")
            f.write(f"Respostas LLM capturadas: {len(self.llm_responses)}\n")
            f.write(f"Cenários testados: {len(scenarios_stats)}\n\n")
            
            # Por cenário
            f.write("🎬 RESULTADOS POR CENÁRIO\n")
            f.write("-" * 25 + "\n")
            for scenario, stats in scenarios_stats.items():
                rate = (stats['success'] / stats['total'] * 100) if stats['total'] > 0 else 0
                f.write(f"{scenario}: {stats['success']}/{stats['total']} ({rate:.1f}%)\n")
            f.write("\n")
            
            # Respostas LLM mais relevantes
            f.write("🤖 RESPOSTAS LLM PRINCIPAIS\n")
            f.write("-" * 25 + "\n")
            for i, response in enumerate(self.llm_responses[:15], 1):
                f.write(f"\n{i}. [{response['scenario']}]\n")
                f.write(f"   Usuário: {response['user_message']}\n")
                f.write(f"   LLM: {response['llm_response'][:150]}...\n")
                f.write(f"   Sistema: {response.get('processing_system', 'unknown')}\n")
                f.write(f"   Confiança: {response.get('confidence', 0)}\n")
            
            # Métricas do sistema
            if final_metrics.get('database'):
                f.write("\n\n📊 MÉTRICAS DO BANCO\n")
                f.write("-" * 20 + "\n")
                db_data = final_metrics['database']
                for table, count in db_data.get('tables_count', {}).items():
                    f.write(f"{table}: {count} registros\n")
                
                if db_data.get('test_user'):
                    user = db_data['test_user']
                    f.write(f"\nUsuário teste: {user.get('nome', 'N/A')}\n")
                    f.write(f"Mensagens: {user.get('total_messages', 0)}\n")
                    f.write(f"Agendamentos: {len(db_data.get('user_appointments', []))}\n")
        
        logger.info(f"📋 Relatório JSON: {json_filename}")
        logger.info(f"📄 Relatório TXT: {txt_filename}")
        logger.info(f"📝 Log detalhado: {log_filename}")
        
        return json_filename, txt_filename

    async def run_complete_test_suite(self):
        """Executa suite completa de testes"""
        logger.info("🚀 INICIANDO SUITE COMPLETA DE TESTES")
        logger.info("🎯 Alvo: WhatsApp Agent - Sistema de Beleza")
        logger.info(f"📱 Telefone: {TEST_PHONE}")
        logger.info(f"🌐 URL: {RAILWAY_URL}")
        logger.info("=" * 60)
        
        # Debug inicial
        await self.debug_system_check()
        
        # Executar todos os cenários
        test_flows = [
            self.test_greeting_flow,
            self.test_service_inquiry_flow,
            self.test_appointment_booking_flow,
            self.test_cancellation_flow,
            self.test_reschedule_flow,
            self.test_complaint_flow,
            self.test_complex_inquiry_flow,
            self.test_business_info_flow,
            self.test_multi_topic_flow,
            self.test_edge_cases_flow
        ]
        
        for i, flow in enumerate(test_flows, 1):
            try:
                logger.info(f"\n▶️ Executando fluxo {i}/{len(test_flows)}")
                await flow()
                logger.info(f"✅ Fluxo {i} concluído")
                
                # Pausa entre fluxos
                if i < len(test_flows):
                    logger.info("⏳ Pausa entre fluxos...")
                    await asyncio.sleep(5.0)
                    
            except Exception as e:
                logger.error(f"❌ Erro no fluxo {i}: {e}")
                continue
        
        # Coletar métricas finais
        final_metrics = await self.collect_final_metrics()
        
        # Gerar relatórios
        json_file, txt_file = await self.generate_comprehensive_report(final_metrics)
        
        # Resumo final
        total_messages = len(self.test_results)
        successful_messages = len([r for r in self.test_results if r.get('status_code') == 200])
        success_rate = (successful_messages / total_messages * 100) if total_messages > 0 else 0
        
        logger.info("\n🎯 TESTE COMPLETO FINALIZADO!")
        logger.info("=" * 40)
        logger.info(f"📊 Mensagens enviadas: {total_messages}")
        logger.info(f"✅ Sucessos: {successful_messages} ({success_rate:.1f}%)")
        logger.info(f"🤖 Respostas LLM capturadas: {len(self.llm_responses)}")
        logger.info(f"⏱️ Duração: {(datetime.now() - self.start_time).total_seconds():.1f}s")
        logger.info(f"📋 Relatórios: {json_file}, {txt_file}")
        
        return final_metrics

async def main():
    """Função principal"""
    logger.info("🧪 WhatsApp Agent - Suite Completa de Testes")
    logger.info("Desenvolvido para análise abrangente do sistema")
    
    async with WhatsAppTester() as tester:
        result = await tester.run_complete_test_suite()
        return result

if __name__ == "__main__":
    asyncio.run(main())
