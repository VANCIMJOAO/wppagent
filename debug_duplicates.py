#!/usr/bin/env python3
"""
Teste específico para detectar duplicatas
"""
import asyncio
import aiohttp
import time
import json
from datetime import datetime

async def test_duplicate_detection():
    print('🔍 DETECTANDO DUPLICATAS EM TEMPO REAL')
    print('=' * 50)
    
    webhook_url = 'https://wppagent-production.up.railway.app/webhook'
    stats_url = 'https://wppagent-production.up.railway.app/webhook/stats'
    
    # Payload de teste
    test_message_id = f'duplicate_test_{int(time.time())}'
    test_payload = {
        'object': 'whatsapp_business_account',
        'entry': [{
            'id': '728348237027885',
            'changes': [{
                'value': {
                    'messaging_product': 'whatsapp',
                    'metadata': {
                        'display_phone_number': '15551536026',
                        'phone_number_id': '728348237027885'
                    },
                    'messages': [{
                        'from': '5516991022255',
                        'id': test_message_id,
                        'timestamp': str(int(time.time())),
                        'text': {'body': 'teste detectar duplicata'},
                        'type': 'text'
                    }],
                    'contacts': [{
                        'profile': {'name': 'Debug Test'},
                        'wa_id': '5516991022255'
                    }]
                },
                'field': 'messages'
            }]
        }]
    }
    
    responses_received = []
    
    async def capture_response(session, attempt_num):
        try:
            start_time = time.time()
            async with session.post(webhook_url, json=test_payload, timeout=20) as response:
                end_time = time.time()
                response_time = end_time - start_time
                
                result = {
                    'attempt': attempt_num,
                    'status': response.status,
                    'response_time': response_time,
                    'timestamp': datetime.now().isoformat()
                }
                
                if response.status == 200:
                    try:
                        result['body'] = await response.text()
                    except:
                        result['body'] = 'No body'
                
                responses_received.append(result)
                print(f'📨 Tentativa {attempt_num}: Status {response.status} em {response_time:.2f}s')
                return result
                
        except Exception as e:
            print(f'❌ Erro na tentativa {attempt_num}: {e}')
            return {'attempt': attempt_num, 'error': str(e)}
    
    # Enviar múltiplas requisições "simultâneas" 
    print('🚀 Enviando 3 requisições simultâneas...')
    async with aiohttp.ClientSession() as session:
        # Capture stats antes
        try:
            async with session.get(stats_url, timeout=10) as response:
                if response.status == 200:
                    before_stats = await response.json()
                    print(f'📊 Antes: {before_stats["stats"]["responses_sent"]} respostas enviadas')
                else:
                    print('⚠️ Não foi possível obter stats antes')
                    before_stats = None
        except Exception as e:
            print(f'⚠️ Erro ao obter stats antes: {e}')
            before_stats = None
        
        # Enviar requisições
        tasks = [capture_response(session, i+1) for i in range(3)]
        await asyncio.gather(*tasks)
        
        # Aguardar processamento
        print('⏳ Aguardando processamento (20s)...')
        await asyncio.sleep(20)
        
        # Capture stats depois
        try:
            async with session.get(stats_url, timeout=10) as response:
                if response.status == 200:
                    after_stats = await response.json()
                    print(f'📊 Depois: {after_stats["stats"]["responses_sent"]} respostas enviadas')
                    
                    if before_stats:
                        diff = after_stats["stats"]["responses_sent"] - before_stats["stats"]["responses_sent"]
                        print(f'🔢 Diferença: {diff} novas respostas')
                        
                        if diff == 1:
                            print('✅ PERFEITO: Apenas 1 resposta enviada!')
                        elif diff > 1:
                            print(f'❌ PROBLEMA: {diff} respostas duplicadas!')
                            
                            # Mostrar detalhes
                            print('\n📋 DETALHES DAS RESPOSTAS:')
                            for i, resp in enumerate(responses_received, 1):
                                print(f'  Tentativa {i}: {resp}')
                        else:
                            print('⚠️ Nenhuma resposta nova detectada')
                    
                    # Mostrar métricas detalhadas
                    print('\n📈 MÉTRICAS DETALHADAS:')
                    for key, value in after_stats['metrics'].items():
                        print(f'  {key}: {value}')
                        
                else:
                    print('⚠️ Não foi possível obter stats depois')
        except Exception as e:
            print(f'❌ Erro ao obter stats depois: {e}')

if __name__ == "__main__":
    asyncio.run(test_duplicate_detection())