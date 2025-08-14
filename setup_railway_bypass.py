#!/usr/bin/env python3
"""
⚙️ CONFIGURAÇÃO RAILWAY - Bypass Webhook
=======================================

Script para ajudar na configuração da variável BYPASS_WEBHOOK_VALIDATION
no Railway para testes completos
"""

import os
import subprocess
import asyncio
import aiohttp

def show_railway_config_instructions():
    """Mostra instruções para configurar no Railway"""
    print("🔧 CONFIGURAÇÃO NO RAILWAY - PASSO A PASSO")
    print("="*60)
    
    print("\n📋 OPÇÃO 1: VIA DASHBOARD WEB")
    print("-"*30)
    print("1. Acesse: https://railway.app")
    print("2. Entre no seu projeto: wppagent")
    print("3. Vá em 'Variables' ou 'Environment'")
    print("4. Adicione nova variável:")
    print("   Nome: BYPASS_WEBHOOK_VALIDATION")
    print("   Valor: true")
    print("5. Clique em 'Deploy' ou 'Save'")
    
    print("\n📋 OPÇÃO 2: VIA RAILWAY CLI")
    print("-"*30)
    print("1. Instale Railway CLI (se não tiver):")
    print("   npm install -g @railway/cli")
    print("2. Execute no terminal:")
    print("   railway login")
    print("   railway environment")
    print("   railway variables set BYPASS_WEBHOOK_VALIDATION=true")

async def test_bypass_status():
    """Testa se o bypass está ativo"""
    print("\n🧪 TESTANDO STATUS DO BYPASS")
    print("-"*40)
    
    try:
        async with aiohttp.ClientSession() as session:
            # Teste simples de webhook
            webhook_payload = {
                "object": "whatsapp_business_account",
                "entry": [{
                    "id": "test_bypass",
                    "changes": [{
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "15551536026",
                                "phone_number_id": "728348237027885"
                            },
                            "contacts": [{
                                "profile": {"name": "Teste Bypass"},
                                "wa_id": "5516991022255"
                            }],
                            "messages": [{
                                "from": "5516991022255",
                                "id": "wamid.test_bypass_123",
                                "timestamp": "1691939000",
                                "type": "text",
                                "text": {"body": "Teste de bypass ativo"}
                            }]
                        },
                        "field": "messages"
                    }]
                }]
            }
            
            async with session.post(
                "https://wppagent-production.up.railway.app/webhook",
                json=webhook_payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                print(f"Status: {response.status}")
                
                if response.status == 200:
                    print("✅ BYPASS ATIVO! Webhook aceito sem validação")
                    return True
                elif response.status == 403:
                    text = await response.text()
                    if "Webhook inválido" in text:
                        print("❌ BYPASS INATIVO - Validação ainda ativa")
                    else:
                        print(f"⚠️ Outro erro 403: {text}")
                    return False
                else:
                    text = await response.text()
                    print(f"⚠️ Status inesperado {response.status}: {text}")
                    return False
                    
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False

async def main():
    """Função principal"""
    print("⚙️ CONFIGURAÇÃO RAILWAY - BYPASS WEBHOOK")
    print("🎯 Objetivo: Ativar testes completos de webhook")
    print("="*60)
    
    # Testar status atual
    print("1️⃣ VERIFICANDO STATUS ATUAL")
    bypass_active = await test_bypass_status()
    
    if bypass_active:
        print("\n🎉 BYPASS JÁ ESTÁ ATIVO!")
        print("✅ Você pode executar os testes completos agora")
        print("🚀 Execute: python3 test_real_whatsapp.py")
        return
    
    # Mostrar instruções
    print("\n2️⃣ CONFIGURAÇÃO NECESSÁRIA")
    show_railway_config_instructions()
    
    print("\n" + "="*60)
    print("📋 PRÓXIMOS PASSOS:")
    print("1. Configure BYPASS_WEBHOOK_VALIDATION=true no Railway")
    print("2. Aguarde o deploy (1-2 minutos)")  
    print("3. Execute: python3 test_real_whatsapp.py")
    print("4. Veja as mensagens chegando no seu WhatsApp!")

if __name__ == "__main__":
    asyncio.run(main())
