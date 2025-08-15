#!/usr/bin/env python3
"""
🔧 DIAGNÓSTICO E CORREÇÃO - Erros Técnicos LLM
=============================================
Identifica e corrige problemas de instabilidade
"""

import asyncio
import asyncpg
import aiohttp
import json
import time
from datetime import datetime, timedelta

class LLMStabilityFixer:
    def __init__(self):
        self.DATABASE_URL = "postgresql://postgres:UGARTPCwAADBBeBLctoRnQXLsoUvLJxz@caboose.proxy.rlwy.net:13910/railway"
        self.API_BASE_URL = "https://wppagent-production.up.railway.app"
        
    async def connect(self):
        """Conecta ao banco"""
        try:
            self.db = await asyncpg.connect(self.DATABASE_URL)
            print("✅ Conectado ao banco PostgreSQL")
            return True
        except Exception as e:
            print(f"❌ Erro ao conectar: {e}")
            return False

    async def analyze_error_patterns(self):
        """Analisa padrões de erro nas mensagens"""
        print("\n🔍 ANALISANDO PADRÕES DE ERRO")
        print("=" * 50)
        
        try:
            # Buscar mensagens com erro técnico
            error_messages = await self.db.fetch("""
                SELECT 
                    m.id, m.content, m.created_at, m.direction,
                    u.wa_id
                FROM messages m
                JOIN users u ON m.user_id = u.id
                WHERE m.content LIKE '%problema técnico%' 
                   OR m.content LIKE '%erro técnico%'
                   OR m.content LIKE '%tive um problema%'
                ORDER BY m.created_at DESC
                LIMIT 20
            """)
            
            print(f"📊 {len(error_messages)} mensagens de erro encontradas")
            
            if error_messages:
                print("\n❌ MENSAGENS DE ERRO RECENTES:")
                for msg in error_messages:
                    print(f"   🕐 {msg['created_at']}: {msg['content'][:50]}...")
                
                # Analisar timing dos erros
                error_times = [msg['created_at'] for msg in error_messages]
                if len(error_times) >= 2:
                    intervals = []
                    for i in range(1, len(error_times)):
                        interval = (error_times[i-1] - error_times[i]).total_seconds()
                        intervals.append(interval)
                    
                    avg_interval = sum(intervals) / len(intervals)
                    print(f"\n📊 Intervalo médio entre erros: {avg_interval:.1f} segundos")
                    
                    if avg_interval < 30:
                        print("⚠️ PROBLEMA: Erros muito frequentes (possível sobrecarga)")
                    else:
                        print("✅ Frequência de erros aceitável")
            
            return error_messages
            
        except Exception as e:
            print(f"❌ Erro ao analisar padrões: {e}")
            return []

    async def check_llm_performance(self):
        """Verifica performance da LLM"""
        print("\n🤖 VERIFICANDO PERFORMANCE DA LLM")
        print("=" * 50)
        
        try:
            # Buscar mensagens das últimas 24h
            yesterday = datetime.now() - timedelta(hours=24)
            
            recent_stats = await self.db.fetchrow("""
                SELECT 
                    COUNT(*) as total_messages,
                    COUNT(CASE WHEN direction = 'in' THEN 1 END) as user_messages,
                    COUNT(CASE WHEN direction = 'out' THEN 1 END) as bot_responses,
                    COUNT(CASE WHEN content LIKE '%problema técnico%' THEN 1 END) as error_responses
                FROM messages m
                JOIN users u ON m.user_id = u.id
                WHERE m.created_at >= $1
                  AND u.wa_id = '5516991022255'
            """, yesterday)
            
            print(f"📊 ESTATÍSTICAS (ÚLTIMAS 24H):")
            print(f"   📨 Total de mensagens: {recent_stats['total_messages']}")
            print(f"   👤 Mensagens do usuário: {recent_stats['user_messages']}")
            print(f"   🤖 Respostas do bot: {recent_stats['bot_responses']}")
            print(f"   ❌ Respostas de erro: {recent_stats['error_responses']}")
            
            if recent_stats['user_messages'] > 0:
                success_rate = ((recent_stats['bot_responses'] - recent_stats['error_responses']) / recent_stats['user_messages']) * 100
                error_rate = (recent_stats['error_responses'] / recent_stats['bot_responses']) * 100 if recent_stats['bot_responses'] > 0 else 0
                
                print(f"   ✅ Taxa de sucesso: {success_rate:.1f}%")
                print(f"   ❌ Taxa de erro: {error_rate:.1f}%")
                
                if error_rate > 20:
                    print("⚠️ CRÍTICO: Taxa de erro muito alta!")
                elif error_rate > 10:
                    print("⚠️ ATENÇÃO: Taxa de erro elevada")
                else:
                    print("✅ Taxa de erro aceitável")
            
            return recent_stats
            
        except Exception as e:
            print(f"❌ Erro ao verificar performance: {e}")
            return None

    async def test_llm_endpoint_health(self):
        """Testa saúde do endpoint da LLM"""
        print("\n🔗 TESTANDO SAÚDE DOS ENDPOINTS")
        print("=" * 50)
        
        endpoints_to_test = [
            "/health",
            "/webhook", 
            "/api/health",
            "/status"
        ]
        
        healthy_endpoints = []
        
        async with aiohttp.ClientSession() as session:
            for endpoint in endpoints_to_test:
                try:
                    url = f"{self.API_BASE_URL}{endpoint}"
                    
                    start_time = time.time()
                    async with session.get(url, timeout=10) as response:
                        response_time = time.time() - start_time
                        
                        if response.status == 200:
                            print(f"✅ {endpoint}: OK ({response_time:.2f}s)")
                            healthy_endpoints.append({
                                "endpoint": endpoint,
                                "status": response.status,
                                "response_time": response_time
                            })
                        else:
                            print(f"⚠️ {endpoint}: {response.status} ({response_time:.2f}s)")
                
                except asyncio.TimeoutError:
                    print(f"⏰ {endpoint}: Timeout (>10s)")
                except Exception as e:
                    print(f"❌ {endpoint}: {str(e)[:50]}")
        
        print(f"\n📊 {len(healthy_endpoints)}/{len(endpoints_to_test)} endpoints saudáveis")
        return healthy_endpoints

    async def test_webhook_with_simple_message(self):
        """Testa webhook com mensagem simples"""
        print("\n🧪 TESTANDO WEBHOOK COM MENSAGEM SIMPLES")
        print("=" * 50)
        
        webhook_url = f"{self.API_BASE_URL}/webhook"
        
        test_payload = {
            "object": "whatsapp_business_account",
            "entry": [{
                "id": "728348237027885",
                "changes": [{
                    "value": {
                        "messaging_product": "whatsapp",
                        "metadata": {
                            "display_phone_number": "16991022255",
                            "phone_number_id": "728348237027885"
                        },
                        "messages": [{
                            "from": "5516991022255",
                            "id": f"test_health_{int(time.time())}",
                            "timestamp": str(int(time.time())),
                            "text": {"body": "teste de saúde"},
                            "type": "text"
                        }]
                    },
                    "field": "messages"
                }]
            }]
        }
        
        try:
            initial_count = await self.db.fetchval(
                "SELECT COUNT(*) FROM messages WHERE user_id = (SELECT id FROM users WHERE wa_id = '5516991022255')"
            )
            
            print(f"📊 Mensagens antes do teste: {initial_count}")
            
            async with aiohttp.ClientSession() as session:
                start_time = time.time()
                async with session.post(webhook_url, json=test_payload, timeout=30) as response:
                    response_time = time.time() - start_time
                    
                    print(f"🔗 Webhook response: {response.status} ({response_time:.2f}s)")
                    
                    if response.status == 200:
                        # Aguardar processamento
                        await asyncio.sleep(5)
                        
                        final_count = await self.db.fetchval(
                            "SELECT COUNT(*) FROM messages WHERE user_id = (SELECT id FROM users WHERE wa_id = '5516991022255')"
                        )
                        
                        print(f"📊 Mensagens após o teste: {final_count}")
                        
                        if final_count > initial_count:
                            # Buscar resposta
                            latest_response = await self.db.fetchrow("""
                                SELECT content, direction, created_at
                                FROM messages m
                                JOIN users u ON m.user_id = u.id
                                WHERE u.wa_id = '5516991022255' 
                                  AND direction = 'out'
                                ORDER BY created_at DESC
                                LIMIT 1
                            """)
                            
                            if latest_response:
                                print(f"✅ Bot respondeu: {latest_response['content'][:100]}...")
                                
                                if "problema técnico" in latest_response['content']:
                                    print("❌ PROBLEMA: Bot retornou erro técnico")
                                    return False
                                else:
                                    print("✅ Bot funcionando corretamente")
                                    return True
                            else:
                                print("⚠️ Nenhuma resposta do bot detectada")
                                return False
                        else:
                            print("⚠️ Mensagem não foi processada")
                            return False
                    else:
                        print(f"❌ Webhook falhou: {response.status}")
                        return False
                        
        except Exception as e:
            print(f"❌ Erro no teste de webhook: {e}")
            return False

    async def generate_recommendations(self, error_messages, performance_stats, webhook_test_result):
        """Gera recomendações baseadas na análise"""
        print("\n💡 RECOMENDAÇÕES DE CORREÇÃO")
        print("=" * 50)
        
        recommendations = []
        
        # Análise de erros
        if len(error_messages) > 5:
            recommendations.append({
                "priority": "HIGH",
                "issue": "Muitos erros técnicos detectados",
                "solution": "Implementar retry logic e tratamento de timeout"
            })
        
        # Análise de performance
        if performance_stats and performance_stats['error_responses'] > 0:
            error_rate = (performance_stats['error_responses'] / performance_stats['bot_responses']) * 100
            
            if error_rate > 20:
                recommendations.append({
                    "priority": "CRITICAL",
                    "issue": f"Taxa de erro muito alta: {error_rate:.1f}%",
                    "solution": "Verificar API OpenAI, implementar fallback"
                })
        
        # Análise do webhook
        if not webhook_test_result:
            recommendations.append({
                "priority": "HIGH", 
                "issue": "Webhook não está processando mensagens corretamente",
                "solution": "Verificar logs do servidor, timeout settings"
            })
        
        # Recomendações gerais
        recommendations.extend([
            {
                "priority": "MEDIUM",
                "issue": "Necessário monitoramento contínuo",
                "solution": "Implementar healthcheck automatizado"
            },
            {
                "priority": "LOW",
                "issue": "Métricas de teste incorretas",
                "solution": "Corrigir cálculo de taxa de sucesso"
            }
        ])
        
        # Exibir recomendações
        for i, rec in enumerate(recommendations, 1):
            priority_color = {
                "CRITICAL": "🔴",
                "HIGH": "🟠", 
                "MEDIUM": "🟡",
                "LOW": "🟢"
            }
            
            print(f"{priority_color[rec['priority']]} {rec['priority']} - {rec['issue']}")
            print(f"   💡 Solução: {rec['solution']}")
            print()
        
        return recommendations

    async def run_complete_analysis(self):
        """Executa análise completa"""
        print("🔧 INICIANDO DIAGNÓSTICO COMPLETO DE ESTABILIDADE")
        print("=" * 60)
        
        if not await self.connect():
            return False
        
        # 1. Analisar padrões de erro
        error_messages = await self.analyze_error_patterns()
        
        # 2. Verificar performance
        performance_stats = await self.check_llm_performance()
        
        # 3. Testar saúde dos endpoints
        healthy_endpoints = await self.test_llm_endpoint_health()
        
        # 4. Testar webhook
        webhook_test = await self.test_webhook_with_simple_message()
        
        # 5. Gerar recomendações
        recommendations = await self.generate_recommendations(
            error_messages, performance_stats, webhook_test
        )
        
        # 6. Relatório final
        print("\n📊 RESUMO DO DIAGNÓSTICO")
        print("=" * 50)
        print(f"❌ Mensagens de erro: {len(error_messages)}")
        print(f"📈 Performance: {'OK' if performance_stats else 'PROBLEMA'}")
        print(f"🔗 Endpoints saudáveis: {len(healthy_endpoints)}")
        print(f"🧪 Teste webhook: {'PASSOU' if webhook_test else 'FALHOU'}")
        print(f"💡 Recomendações: {len(recommendations)}")
        
        # Salvar relatório
        report = {
            "timestamp": datetime.now().isoformat(),
            "error_count": len(error_messages),
            "performance_stats": dict(performance_stats) if performance_stats else None,
            "healthy_endpoints": healthy_endpoints,
            "webhook_test_passed": webhook_test,
            "recommendations": recommendations
        }
        
        filename = f"llm_stability_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n📄 Relatório salvo: {filename}")
        
        return True

    async def close(self):
        """Fecha conexão"""
        try:
            if hasattr(self, 'db'):
                await self.db.close()
                print("✅ Conexão fechada")
        except Exception as e:
            print(f"❌ Erro ao fechar: {e}")


async def main():
    """Função principal"""
    fixer = LLMStabilityFixer()
    
    try:
        await fixer.run_complete_analysis()
    except KeyboardInterrupt:
        print("\n⏹️ Análise interrompida")
    except Exception as e:
        print(f"\n💥 Erro: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await fixer.close()


if __name__ == "__main__":
    print("🔧 DIAGNÓSTICO DE ESTABILIDADE - LLM WhatsApp")
    print("=" * 60)
    print("🎯 Problemas identificados:")
    print("   ❌ 'Desculpe, tive um problema técnico'")
    print("   ❌ Bot falha após várias mensagens")
    print("   ❌ Instabilidade na LLM")
    print("\n✅ Este script vai:")
    print("   🔍 Analisar padrões de erro")
    print("   📊 Verificar performance da LLM")
    print("   🧪 Testar estabilidade do webhook")
    print("   💡 Gerar recomendações de correção")
    print("=" * 60)
    
    input("▶️ Pressione ENTER para iniciar análise...")
    
    asyncio.run(main())