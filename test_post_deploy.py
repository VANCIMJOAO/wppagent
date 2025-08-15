#!/usr/bin/env python3
"""
🎯 TESTE PÓS-DEPLOY - Verificação 100% Formatação
===============================================
Testa se as melhorias implementadas alcançaram 100% de formatação
"""

import asyncio
import asyncpg
import aiohttp
import time
from datetime import datetime

async def test_post_deploy_formatting():
    """Testa formatação após deploy das melhorias"""
    
    try:
        db = await asyncpg.connect('postgresql://postgres:UGARTPCwAADBBeBLctoRnQXLsoUvLJxz@caboose.proxy.rlwy.net:13910/railway')
        print('🎯 TESTE PÓS-DEPLOY - FORMATAÇÃO MELHORADA')
        print('=' * 50)
        
        tests = [
            ("Qual o horário de funcionamento?", "HORÁRIOS", ["🏢", "🕘", "🚫", "*", "_"]),
            ("Onde vocês ficam localizados?", "LOCALIZAÇÃO", ["🏢", "📍", "📞", "📧", "*", "_"])
        ]
        
        total_improvements = 0
        
        for question, test_name, key_elements in tests:
            print(f'\\n🔍 {test_name}...')
            
            webhook_data = {
                'object': 'whatsapp_business_account',
                'entry': [{
                    'id': '106123875816964',
                    'changes': [{
                        'value': {
                            'messaging_product': 'whatsapp',
                            'metadata': {
                                'display_phone_number': '15551536026',
                                'phone_number_id': '728348237027885'
                            },
                            'messages': [{
                                'from': '5516991022255',
                                'id': f'wamid.test_{int(time.time())}',
                                'timestamp': str(int(time.time())),
                                'text': {'body': question},
                                'type': 'text'
                            }]
                        },
                        'field': 'messages'
                    }]
                }]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post('https://wppagent-production.up.railway.app/webhook', 
                                      json=webhook_data, timeout=30) as response:
                    print(f'   Status: {response.status}')
                        
            await asyncio.sleep(8)
            
            recent_responses = await db.fetch(\"\"\"
                SELECT direction, content, created_at, message_type
                FROM messages 
                WHERE user_id = 2 
                AND direction = 'out'
                AND created_at > NOW() - INTERVAL '1 minute'
                ORDER BY created_at DESC
                LIMIT 2
            \"\"\")
            
            if not recent_responses:
                print(f'   ❌ Sem resposta')
                continue
                
            bot_response = recent_responses[0]['content']
            print(f'   📱 Resposta ({len(bot_response)} chars):')
            print(f'   {bot_response[:100]}...')
            
            found = []
            for element in key_elements:
                count = bot_response.count(element)
                if count > 0:
                    found.append(f'{element}:{count}x')
            
            percentage = (len(found) / len(key_elements)) * 100
            print(f'   📊 {percentage:.1f}% ({len(found)}/{len(key_elements)})')
            print(f'   ✅ {", ".join(found)}')
            
            # Verificar melhorias específicas
            if test_name == "HORÁRIOS":
                if '🏢' in bot_response and '_' in bot_response:
                    print('   🎉 MELHORIA COMPLETA: 🏢 + itálicos detectados!')
                    total_improvements += 2
                elif '🏢' in bot_response:
                    print('   ✅ Emoji 🏢 detectado!')
                    total_improvements += 1
                elif '_' in bot_response:
                    print('   ✅ Itálicos detectados!')
                    total_improvements += 1
                    
            elif test_name == "LOCALIZAÇÃO":
                italic_count = bot_response.count('_')
                if italic_count >= 4:  # Esperamos pelo menos 2 pares de _
                    print(f'   🎉 ITÁLICOS MELHORADOS: {italic_count//2} elementos!')
                    total_improvements += 1
            
            await asyncio.sleep(3)
        
        print('\\n' + '=' * 50)
        print('🏆 RESULTADO FINAL')
        print('=' * 50)
        
        if total_improvements >= 3:
            print(f'🎉 SUCESSO COMPLETO! {total_improvements} melhorias detectadas!')
            print('✅ Deploy funcionou perfeitamente!')
        elif total_improvements >= 1:
            print(f'✅ MELHORIAS PARCIAIS: {total_improvements} detectadas')
            print('🔄 Algumas mudanças aplicadas com sucesso')
        else:
            print('⚠️  Nenhuma melhoria detectada ainda')
            print('🔄 Deploy pode ainda estar processando...')
        
        await db.close()
        
    except Exception as e:
        print(f'❌ Erro: {e}')

if __name__ == "__main__":
    print("🚀 Testando melhorias pós-deploy...")
    asyncio.run(test_post_deploy_formatting())
