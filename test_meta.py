import asyncio
import json
import time
from datetime import datetime
from typing import Dict, Any
import aiohttp
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WhatsAppAPITester:
    def __init__(self):
        # Configurações do seu Railway
        self.base_url = "https://wppagent-production.up.railway.app"
        self.phone_number_id = "728348237027885"
        self.access_token = "EAAI4WnfpZAe0BPE5kre60eGfUxa1yxtlqERWxJulhIfoR55EUPBiSJb31n9qVbjPnMZC2aHDaG2eD7ZCYShcyH5nqjZCmevSTZCxqSzcAQ32f8tdZBUmay5DQRZBm2oPw08qoL9hSmcSIb3p1nSWqSD990akpw757yDkfVzkVra2F26x2NFW9aV5MDBNZAmfjsfEZB8MwZC5pa9Y7lZBZA5CJCZAsR7rcrvm6VWgp8uQCMD3kz6p4AjeRchZBVgeCv9gZDZD"
        self.your_phone = "5516991022255"
        self.meta_api_base = "https://graph.facebook.com/v21.0"
        
    async def test_railway_endpoints(self):
        """Testa endpoints internos do Railway"""
        logger.info("🔍 TESTANDO ENDPOINTS DO RAILWAY")
        logger.info("=" * 50)
        
        endpoints = [
            "/health",
            "/webhook/status",
            "/metrics/system",
            "/rate-limit/stats"
        ]
        
        results = {}
        
        async with aiohttp.ClientSession() as session:
            for endpoint in endpoints:
                try:
                    url = f"{self.base_url}{endpoint}"
                    logger.info(f"📡 Testando: {endpoint}")
                    
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                        status = response.status
                        text = await response.text()
                        
                        results[endpoint] = {
                            "status": status,
                            "success": status == 200,
                            "response": text[:500] if text else ""
                        }
                        
                        if status == 200:
                            logger.info(f"  ✅ {endpoint}: OK")
                        else:
                            logger.warning(f"  ⚠️ {endpoint}: HTTP {status}")
                            
                except Exception as e:
                    results[endpoint] = {
                        "status": 0,
                        "success": False,
                        "error": str(e)
                    }
                    logger.error(f"  ❌ {endpoint}: {str(e)}")
        
        return results
    
    async def test_meta_api_direct(self):
        """Testa a Meta API diretamente"""
        logger.info("\n🌐 TESTANDO META API DIRETAMENTE")
        logger.info("=" * 50)
        
        # Teste 1: Verificar se o token está válido
        logger.info("🔑 Verificando validade do token...")
        
        token_valid = await self._check_token_validity()
        if not token_valid:
            logger.error("❌ Token de acesso inválido!")
            return {"token_valid": False}
        
        logger.info("✅ Token válido!")
        
        # Teste 2: Tentar enviar mensagem diretamente
        logger.info("📤 Tentando enviar mensagem diretamente via Meta API...")
        
        message_result = await self._send_direct_message("🧪 TESTE: Mensagem enviada diretamente via Meta API")
        
        return {
            "token_valid": token_valid,
            "direct_message": message_result
        }
    
    async def _check_token_validity(self):
        """Verifica se o token de acesso está válido"""
        try:
            url = f"{self.meta_api_base}/me?access_token={self.access_token}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"📋 Token válido para: {data.get('name', 'N/A')}")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Token inválido: HTTP {response.status} - {error_text}")
                        return False
                        
        except Exception as e:
            logger.error(f"❌ Erro ao verificar token: {e}")
            return False
    
    async def _send_direct_message(self, message: str):
        """Envia mensagem diretamente via Meta API"""
        try:
            url = f"{self.meta_api_base}/{self.phone_number_id}/messages"
            
            payload = {
                "messaging_product": "whatsapp",
                "to": self.your_phone,
                "type": "text",
                "text": {
                    "body": message
                }
            }
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url, 
                    json=payload, 
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    
                    status = response.status
                    response_data = await response.json()
                    
                    if status == 200:
                        logger.info("✅ Mensagem enviada diretamente com sucesso!")
                        logger.info(f"📋 Message ID: {response_data.get('messages', [{}])[0].get('id', 'N/A')}")
                        return {
                            "success": True,
                            "status": status,
                            "response": response_data
                        }
                    else:
                        logger.error(f"❌ Falha ao enviar: HTTP {status}")
                        logger.error(f"📋 Erro: {response_data}")
                        return {
                            "success": False,
                            "status": status,
                            "error": response_data
                        }
                        
        except Exception as e:
            logger.error(f"❌ Exceção ao enviar mensagem: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def test_railway_send_endpoint(self):
        """Testa o endpoint de envio do Railway"""
        logger.info("\n🚀 TESTANDO ENDPOINT DE ENVIO DO RAILWAY")
        logger.info("=" * 50)
        
        test_url = f"{self.base_url}/webhook/test-send"
        
        params = {
            "phone_number": self.your_phone,
            "message": "🧪 TESTE: Mensagem via endpoint Railway"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    test_url,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    
                    status = response.status
                    response_data = await response.json()
                    
                    logger.info(f"📡 Status: HTTP {status}")
                    logger.info(f"📋 Resposta: {json.dumps(response_data, indent=2)}")
                    
                    return {
                        "status": status,
                        "success": status == 200,
                        "response": response_data
                    }
                    
        except Exception as e:
            logger.error(f"❌ Erro no teste de envio: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def check_railway_logs(self):
        """Verifica logs e configurações do Railway"""
        logger.info("\n📊 VERIFICANDO STATUS DO RAILWAY")
        logger.info("=" * 50)
        
        # Verificar health checks
        health_result = await self._check_health()
        
        # Verificar webhook status
        webhook_result = await self._check_webhook_status()
        
        return {
            "health": health_result,
            "webhook": webhook_result
        }
    
    async def _check_health(self):
        """Verifica health check detalhado"""
        try:
            url = f"{self.base_url}/health/detailed"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        overall_status = data.get("overall_status", "unknown")
                        
                        logger.info(f"🏥 Health Status: {overall_status}")
                        
                        checks = data.get("checks", {})
                        for check_name, check_data in checks.items():
                            status = check_data.get("status", "unknown")
                            message = check_data.get("message", "")
                            logger.info(f"  📋 {check_name}: {status} - {message}")
                        
                        return {"success": True, "data": data}
                    else:
                        return {"success": False, "status": response.status}
                        
        except Exception as e:
            logger.error(f"❌ Erro no health check: {e}")
            return {"success": False, "error": str(e)}
    
    async def _check_webhook_status(self):
        """Verifica status específico do webhook"""
        try:
            url = f"{self.base_url}/webhook/status"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        webhook_status = data.get("webhook_status", "unknown")
                        meta_api = data.get("meta_api", {})
                        
                        logger.info(f"🔗 Webhook Status: {webhook_status}")
                        logger.info(f"🌐 Meta API Status: {meta_api.get('status', 'unknown')}")
                        
                        if meta_api.get("fallback_queue_size", 0) > 0:
                            logger.warning(f"⚠️ Fila de fallback: {meta_api['fallback_queue_size']} mensagens")
                        
                        return {"success": True, "data": data}
                    else:
                        return {"success": False, "status": response.status}
                        
        except Exception as e:
            logger.error(f"❌ Erro no webhook status: {e}")
            return {"success": False, "error": str(e)}
    
    async def run_complete_diagnosis(self):
        """Executa diagnóstico completo"""
        logger.info("🔬 DIAGNÓSTICO COMPLETO - BOT WHATSAPP")
        logger.info("=" * 60)
        logger.info(f"📱 Seu telefone: {self.your_phone}")
        logger.info(f"🆔 Phone Number ID: {self.phone_number_id}")
        logger.info(f"🌐 Railway URL: {self.base_url}")
        logger.info("=" * 60)
        
        results = {}
        
        # 1. Testar endpoints do Railway
        results["railway_endpoints"] = await self.test_railway_endpoints()
        
        # 2. Verificar status do Railway
        results["railway_status"] = await self.check_railway_logs()
        
        # 3. Testar Meta API diretamente
        results["meta_api_direct"] = await self.test_meta_api_direct()
        
        # 4. Testar endpoint de envio do Railway
        results["railway_send"] = await self.test_railway_send_endpoint()
        
        # 5. Gerar relatório
        await self.generate_diagnosis_report(results)
        
        return results
    
    async def generate_diagnosis_report(self, results: Dict[str, Any]):
        """Gera relatório de diagnóstico"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Análise dos resultados
        issues = []
        successes = []
        
        # Verificar endpoints Railway
        railway_endpoints = results.get("railway_endpoints", {})
        working_endpoints = sum(1 for r in railway_endpoints.values() if r.get("success", False))
        total_endpoints = len(railway_endpoints)
        
        if working_endpoints == total_endpoints:
            successes.append("✅ Todos os endpoints do Railway funcionando")
        else:
            issues.append(f"⚠️ {total_endpoints - working_endpoints} endpoints com problema")
        
        # Verificar Meta API
        meta_direct = results.get("meta_api_direct", {})
        if meta_direct.get("token_valid", False):
            successes.append("✅ Token Meta API válido")
        else:
            issues.append("❌ Token Meta API inválido ou expirado")
        
        if meta_direct.get("direct_message", {}).get("success", False):
            successes.append("✅ Meta API funcionando - mensagem enviada diretamente")
        else:
            issues.append("❌ Meta API não consegue enviar mensagens")
        
        # Verificar Railway send
        railway_send = results.get("railway_send", {})
        if railway_send.get("success", False):
            successes.append("✅ Endpoint de envio do Railway funcionando")
        else:
            issues.append("❌ Endpoint de envio do Railway com problema")
        
        # Relatório
        report = f"""
🔬 RELATÓRIO DE DIAGNÓSTICO - BOT WHATSAPP
{'='*70}

📊 RESUMO:
• Data/Hora: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}
• Telefone testado: {self.your_phone}
• Railway URL: {self.base_url}
• Phone Number ID: {self.phone_number_id}

🎯 PROBLEMAS IDENTIFICADOS:
"""
        
        if issues:
            for issue in issues:
                report += f"  {issue}\n"
        else:
            report += "  🎉 Nenhum problema identificado!\n"
        
        report += f"""
✅ FUNCIONANDO CORRETAMENTE:
"""
        for success in successes:
            report += f"  {success}\n"
        
        report += f"""
{'='*70}
📋 DETALHES TÉCNICOS:

🔗 ENDPOINTS RAILWAY:
"""
        for endpoint, data in railway_endpoints.items():
            status = "✅" if data.get("success") else "❌"
            report += f"  {status} {endpoint}: HTTP {data.get('status', 'ERROR')}\n"
        
        report += f"""
🌐 META API:
• Token válido: {"✅ Sim" if meta_direct.get("token_valid") else "❌ Não"}
• Envio direto: {"✅ OK" if meta_direct.get("direct_message", {}).get("success") else "❌ FALHOU"}
"""
        
        if meta_direct.get("direct_message", {}).get("error"):
            report += f"• Erro Meta API: {meta_direct['direct_message']['error']}\n"
        
        report += f"""
🚀 RAILWAY SEND:
• Status: {"✅ OK" if railway_send.get("success") else "❌ FALHOU"}
"""
        
        if railway_send.get("error"):
            report += f"• Erro Railway: {railway_send['error']}\n"
        
        report += f"""
{'='*70}
🔧 RECOMENDAÇÕES:

"""
        
        if not meta_direct.get("token_valid", False):
            report += """❗ CRÍTICO: Token Meta API inválido
  • Verifique se o token não expirou
  • Gere um novo token no Meta Developers Console
  • Atualize a variável META_ACCESS_TOKEN no Railway

"""
        
        if not meta_direct.get("direct_message", {}).get("success", False):
            report += """❗ CRÍTICO: Meta API não está enviando mensagens
  • Verifique se o Phone Number ID está correto
  • Confirme se o número de teste está cadastrado no Meta Business
  • Verifique limitações da conta (sandbox vs production)

"""
        
        if not railway_send.get("success", False):
            report += """⚠️ IMPORTANTE: Endpoint de envio do Railway com problema
  • Verifique logs do Railway para erros
  • Confirme se as variáveis de ambiente estão configuradas
  • Teste a conectividade entre Railway e Meta API

"""
        
        if len(issues) == 0:
            report += """🎉 TUDO FUNCIONANDO!
  • Seu bot está configurado corretamente
  • O problema pode ser temporário ou de rede
  • Teste novamente enviando uma mensagem real

"""
        
        report += f"{'='*70}\n"
        
        # Salvar relatório
        filename = f"whatsapp_diagnosis_report_{timestamp}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)
        
        # Salvar JSON detalhado
        json_filename = f"whatsapp_diagnosis_data_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(report)
        logger.info(f"📄 Relatórios salvos:")
        logger.info(f"  • Diagnóstico: {filename}")
        logger.info(f"  • Dados JSON: {json_filename}")

async def main():
    """Função principal"""
    tester = WhatsAppAPITester()
    
    print("🔬 DIAGNÓSTICO DO BOT WHATSAPP")
    print("=" * 40)
    print("Este script vai:")
    print("• Testar todos os endpoints do Railway")
    print("• Verificar a Meta API diretamente")
    print("• Tentar enviar mensagem real")
    print("• Identificar onde está o problema")
    print("=" * 40)
    
    confirm = input("▶️ Continuar com o diagnóstico? (s/n): ")
    if confirm.lower() in ['s', 'sim', 'y', 'yes']:
        await tester.run_complete_diagnosis()
        print("\n🎯 PRÓXIMO PASSO:")
        print("• Verifique seu WhatsApp para mensagens de teste")
        print("• Leia o relatório gerado")
        print("• Siga as recomendações para corrigir problemas")
    else:
        print("❌ Diagnóstico cancelado.")

if __name__ == "__main__":
    asyncio.run(main())