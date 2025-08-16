#!/usr/bin/env python3
"""
🎯 TESTE FINAL PÓS-CORREÇÃO - Formatação WhatsApp
===============================================
Testa se a correção crítica de formatação funcionou em produção
"""

import asyncio
import asyncpg
import aiohttp
import time
from datetime import datetime
import json

async def test_formatting_post_correction():
    """
    Teste final após correção crítica da formatação
    """
    print("🎯 TESTE FINAL PÓS-CORREÇÃO - Formatação WhatsApp")
    print("=" * 60)
    print("🔧 Correção implementada: Quebras de linha preservadas")
    print("📊 Expectativa: 95%+ de formatação perfeita")
    print("=" * 60)
    
    try:
        # Conectar ao banco
        db = await asyncpg.connect("postgresql://postgres:UGARTPCwAADBBeBLctoRnQXLsoUvLJxz@caboose.proxy.rlwy.net:13910/railway")
        
        tests = [
            ("Quais serviços vocês oferecem?", "SERVIÇOS"),
            ("Qual o horário de funcionamento?", "HORÁRIOS"),
            ("Onde vocês ficam localizados?", "LOCALIZAÇÃO")
        ]
        
        results = []
        
        for question, test_name in tests:
            print(f"\n🔍 Testando {test_name}...")
            
            # Enviar mensagem via webhook
            url = "https://wppagent-production.up.railway.app/webhook"
            webhook_data = {
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
                                "from": "5516991022255",
                                "id": f"wamid.test_{int(time.time())}",
                                "timestamp": str(int(time.time())),
                                "text": {"body": question},
                                "type": "text"
                            }]
                        },
                        "field": "messages"
                    }]
                }]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=webhook_data, timeout=30) as response:
                    print(f"  📡 Status: {response.status}")
            
            # Aguardar processamento
            await asyncio.sleep(8)
            
            # Buscar resposta mais recente
            recent_responses = await db.fetch("""
                SELECT direction, content, created_at, message_type
                FROM messages
                WHERE user_id = 2
                AND direction = 'out'
                AND created_at > NOW() - INTERVAL '2 minutes'
                ORDER BY created_at DESC
                LIMIT 1
            """)
            
            if recent_responses:
                bot_response = recent_responses[0]['content']
                print(f"  📱 Resposta: {len(bot_response)} chars")
                
                # Analisar formatação específica por contexto
                if test_name == "SERVIÇOS":
                    # Elementos críticos para serviços
                    key_elements = [
                        '📋', '💰', '⏰', 'ℹ️', '📞',  # Emojis
                        '*', '_',  # Formatação
                        '1.', '2.', '•',  # Estrutura
                        '\n\n'  # 🔥 CRÍTICO: Quebras duplas
                    ]
                elif test_name == "HORÁRIOS":
                    # Elementos críticos para horários
                    key_elements = [
                        '🏢', '🕘', '🚫',  # Emojis
                        '*', '_',  # Formatação
                        '\n', '-'  # Estrutura
                    ]
                elif test_name == "LOCALIZAÇÃO":
                    # Elementos críticos para localização
                    key_elements = [
                        '🏢', '📍', '📞', '📧',  # Emojis
                        '*', '_',  # Formatação
                        '\n'  # Estrutura
                    ]
                
                # Contar elementos encontrados
                found_elements = []
                total_count = 0
                
                for element in key_elements:
                    count = bot_response.count(element)
                    total_count += count
                    if count > 0:
                        found_elements.append(f"{element}:{count}x")
                
                # Calcular porcentagem baseada na presença de elementos
                found_unique = len([e for e in key_elements if e in bot_response])
                percentage = (found_unique / len(key_elements)) * 100
                
                print(f"  📊 Cobertura: {percentage:.1f}% ({found_unique}/{len(key_elements)})")
                print(f"  ✅ Elementos: {found_elements}")
                
                # 🔥 VERIFICAÇÃO CRÍTICA: Quebras de linha
                line_breaks = bot_response.count('\n')
                if line_breaks > 0:
                    print(f"  🎉 QUEBRAS PRESERVADAS: {line_breaks} quebras de linha!")
                else:
                    print(f"  ❌ PROBLEMA: Nenhuma quebra de linha encontrada!")
                
                results.append({
                    "test": test_name,
                    "percentage": percentage,
                    "found_elements": found_unique,
                    "total_elements": len(key_elements),
                    "line_breaks": line_breaks,
                    "response_length": len(bot_response)
                })
                
                await asyncio.sleep(3)
            else:
                print("  ❌ Sem resposta")
        
        # Resultado final
        print(f"\n🏆 RESULTADO FINAL PÓS-CORREÇÃO")
        print("=" * 50)
        
        if results:
            avg_percentage = sum(r["percentage"] for r in results) / len(results)
            total_line_breaks = sum(r["line_breaks"] for r in results)
            
            print(f"📊 FORMATAÇÃO MÉDIA: {avg_percentage:.1f}%")
            print(f"🔥 QUEBRAS DE LINHA TOTAL: {total_line_breaks}")
            print()
            
            for result in results:
                line_status = "🎉" if result["line_breaks"] > 5 else "⚠️" if result["line_breaks"] > 0 else "❌"
                status = "🎉" if result["percentage"] >= 90 else "✅" if result["percentage"] >= 80 else "👍" if result["percentage"] >= 70 else "⚠️"
                
                print(f"{status} {result['test']}: {result['percentage']:.1f}% | {line_status} {result['line_breaks']} quebras")
            
            print()
            
            # Análise da correção
            if total_line_breaks >= 15:  # Esperamos pelo menos 15 quebras no total
                print("🎉 CORREÇÃO FUNCIONOU PERFEITAMENTE!")
                print("✅ Quebras de linha preservadas com sucesso")
                print("✅ Formatação WhatsApp completamente funcional")
                
                if avg_percentage >= 90:
                    print("🏆 EXCELÊNCIA: Formatação quase perfeita!")
                elif avg_percentage >= 80:
                    print("🥇 SUCESSO: Formatação de alta qualidade!")
                else:
                    print("👍 BOM: Formatação funcional e melhorada!")
                
            elif total_line_breaks > 0:
                print("⚠️ CORREÇÃO PARCIAL: Algumas quebras preservadas")
                print("🔍 Verificar se todas as mudanças foram deployadas")
                
            else:
                print("❌ CORREÇÃO NÃO FUNCIONOU: Quebras ainda sendo removidas")
                print("🚨 Verificar deployment ou outras sanitizações")
            
            print(f"\n📈 COMPARAÇÃO:")
            print(f"  Antes da correção: ~0 quebras, 70% formatação")
            print(f"  Após correção: {total_line_breaks} quebras, {avg_percentage:.1f}% formatação")
            print(f"  Melhoria: +{total_line_breaks} quebras, +{avg_percentage-70:.1f} pontos")
        
        await db.close()
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_formatting_post_correction())
