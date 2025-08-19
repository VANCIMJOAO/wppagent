#!/usr/bin/env python3
"""
🔍 TESTE DE DIAGNÓSTICO - PROCESSAMENTO DE MENSAGENS
===================================================
Verifica especificamente o processamento de mensagens no webhook
"""

import asyncio
import aiohttp
import asyncpg
import json
import time
import os
from datetime import datetime, timedelta

# Carregar .env
def load_env():
    with open('.env', 'r') as f:
        for line in f:
            if line.strip() and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip().strip('"').strip("'")

load_env()

class MessageProcessingDiagnostic:
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        self.railway_url = os.getenv('RAILWAY_URL', 'https://wppagent-production.up.railway.app')
        
    async def run_diagnostic(self):
        print("🔍 DIAGNÓSTICO DE PROCESSAMENTO DE MENSAGENS")
        print("=" * 60)
        
        # Conectar ao banco
        self.conn = await asyncpg.connect(self.database_url)
        
        try:
            # 1. Verificar estado inicial
            await self.check_initial_state()
            
            # 2. Testar webhook
            webhook_response = await self.test_webhook_response()
            
            # 3. Testar processamento específico
            await self.test_message_processing()
            
            # 4. Verificar banco após webhook
            await self.check_final_state()
            
            # 5. Diagnóstico de problemas
            await self.diagnose_issues()
            
        finally:
            await self.conn.close()
    
    async def check_initial_state(self):
        """Verificar estado inicial do banco"""
        print("\n📊 ESTADO INICIAL:")
        
        # Contar usuários
        users_count = await self.conn.fetchval("SELECT COUNT(*) FROM users")
        print(f"   👤 Usuários: {users_count}")
        
        # Contar mensagens da última hora
        messages_count = await self.conn.fetchval("""
            SELECT COUNT(*) FROM messages 
            WHERE created_at > NOW() - INTERVAL '1 hour'
        """)
        print(f"   📨 Mensagens (última hora): {messages_count}")
        
        # Verificar usuário de teste
        test_user = await self.conn.fetchrow("""
            SELECT id, nome, telefone, wa_id 
            FROM users 
            WHERE telefone = '5516991022255' OR wa_id = '5516991022255'
        """)
        
        if test_user:
            print(f"   ✅ Usuário teste existe: ID {test_user['id']} - {test_user['nome']}")
            
            # Mensagens deste usuário
            user_messages = await self.conn.fetchval("""
                SELECT COUNT(*) FROM messages 
                WHERE user_id = $1 AND created_at > NOW() - INTERVAL '1 hour'
            """, test_user['id'])
            print(f"   📨 Mensagens do usuário teste (última hora): {user_messages}")
        else:
            print("   ⚠️ Usuário teste não existe")
    
    async def test_webhook_response(self):
        """Testar resposta do webhook"""
        print(f"\n🚀 TESTANDO WEBHOOK RAILWAY: {self.railway_url}")
        
        webhook_data = {
            "object": "whatsapp_business_account",
            "entry": [{
                "id": "test_entry",
                "changes": [{
                    "value": {
                        "messaging_product": "whatsapp",
                        "contacts": [{
                            "profile": {"name": "João Victor Vancim"},
                            "wa_id": "5516991022255"
                        }],
                        "messages": [{
                            "from": "5516991022255",
                            "id": f"diagnostic_msg_{int(time.time())}",
                            "text": {"body": f"Teste diagnóstico Railway {datetime.now().strftime('%H:%M:%S')}"},
                            "timestamp": str(int(time.time())),
                            "type": "text"
                        }]
                    },
                    "field": "messages"
                }]
            }]
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                start_time = time.time()
                
                async with session.post(
                    f'{self.railway_url}/webhook',
                    json=webhook_data,
                    headers={
                        'Content-Type': 'application/json',
                        'User-Agent': 'WhatsApp-Test-Agent/1.0'
                    },
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    duration = time.time() - start_time
                    
                    print(f"   📤 Status: {response.status}")
                    print(f"   ⏱️ Tempo: {duration:.2f}s")
                    
                    if response.status == 200:
                        response_text = await response.text()
                        print(f"   📥 Response: {response_text}")
                        return True
                    else:
                        error_text = await response.text()
                        print(f"   ❌ Erro: {error_text}")
                        return False
                        
        except Exception as e:
            print(f"   💥 Erro no webhook: {e}")
            return False
    
    async def test_message_processing(self):
        """Testar processamento específico de mensagem"""
        print("\n🔧 TESTANDO PROCESSAMENTO:")
        
        # Aguardar um pouco para processamento
        print("   ⏳ Aguardando 3 segundos para processamento...")
        await asyncio.sleep(3)
        
        # Verificar se nova mensagem foi criada
        recent_messages = await self.conn.fetch("""
            SELECT id, user_id, direction, content, created_at
            FROM messages 
            WHERE created_at > NOW() - INTERVAL '30 seconds'
            ORDER BY created_at DESC
        """)
        
        print(f"   📨 Mensagens dos últimos 30s: {len(recent_messages)}")
        
        for msg in recent_messages:
            direction_icon = "📤" if msg['direction'] == 'out' else "📥"
            print(f"      {direction_icon} ID {msg['id']}: {msg['content'][:50]}...")
    
    async def check_final_state(self):
        """Verificar estado final"""
        print("\n📊 ESTADO FINAL:")
        
        # Contar mensagens da última hora novamente
        messages_count = await self.conn.fetchval("""
            SELECT COUNT(*) FROM messages 
            WHERE created_at > NOW() - INTERVAL '1 hour'
        """)
        print(f"   📨 Total mensagens (última hora): {messages_count}")
        
        # Mensagens por direção
        in_messages = await self.conn.fetchval("""
            SELECT COUNT(*) FROM messages 
            WHERE direction = 'in' AND created_at > NOW() - INTERVAL '10 minutes'
        """)
        out_messages = await self.conn.fetchval("""
            SELECT COUNT(*) FROM messages 
            WHERE direction = 'out' AND created_at > NOW() - INTERVAL '10 minutes'
        """)
        
        print(f"   📥 Mensagens recebidas (10 min): {in_messages}")
        print(f"   📤 Mensagens enviadas (10 min): {out_messages}")
        
    async def diagnose_issues(self):
        """Diagnosticar possíveis problemas"""
        print("\n🔍 DIAGNÓSTICO DE PROBLEMAS:")
        
        # 1. Verificar logs do sistema
        try:
            meta_logs = await self.conn.fetch("""
                SELECT endpoint, status_code, created_at, payload
                FROM meta_logs 
                WHERE created_at > NOW() - INTERVAL '10 minutes'
                AND endpoint = '/webhook'
                ORDER BY created_at DESC 
                LIMIT 5
            """)
            
            print(f"   📋 Logs do webhook (10 min): {len(meta_logs)}")
            for log in meta_logs:
                print(f"      {log['created_at']}: {log['status_code']} - {log['endpoint']}")
                
        except Exception as e:
            print(f"   ⚠️ Erro ao verificar logs: {e}")
        
        # 2. Verificar conversas
        try:
            conversations = await self.conn.fetch("""
                SELECT id, user_id, status, updated_at
                FROM conversations 
                WHERE updated_at > NOW() - INTERVAL '1 hour'
                ORDER BY updated_at DESC
                LIMIT 5
            """)
            
            print(f"   💬 Conversas ativas (1h): {len(conversations)}")
            for conv in conversations:
                print(f"      Conv {conv['id']}: User {conv['user_id']}, Status: {conv['status']}")
                
        except Exception as e:
            print(f"   ⚠️ Erro ao verificar conversas: {e}")
        
        # 3. Verificar problemas comuns
        print("\n🔧 VERIFICAÇÕES ESPECÍFICAS:")
        
        # Verificar se há mensagens "orfãs" (sem user_id válido)
        orphan_messages = await self.conn.fetchval("""
            SELECT COUNT(*) FROM messages m
            LEFT JOIN users u ON m.user_id = u.id
            WHERE u.id IS NULL AND m.created_at > NOW() - INTERVAL '1 hour'
        """)
        
        if orphan_messages > 0:
            print(f"   ❌ Mensagens órfãs: {orphan_messages}")
        else:
            print(f"   ✅ Sem mensagens órfãs")
        
        # Verificar rate limiting
        recent_blocks = await self.conn.fetchval("""
            SELECT COUNT(*) FROM messages 
            WHERE created_at > NOW() - INTERVAL '5 minutes'
            AND direction = 'in'
        """)
        
        if recent_blocks > 5:
            print(f"   ⚠️ Muitas mensagens recentes: {recent_blocks} (possível rate limiting)")
        else:
            print(f"   ✅ Rate limiting OK: {recent_blocks} mensagens")
    
    async def test_webhook_status(self):
        """Testar endpoints de status do webhook"""
        print(f"\n📊 TESTANDO STATUS DO WEBHOOK RAILWAY: {self.railway_url}")
        
        endpoints = [
            "/webhook/status",
            "/webhook/stats", 
            "/webhook/control",
            "/status",
            "/health"
        ]
        
        async with aiohttp.ClientSession() as session:
            for endpoint in endpoints:
                try:
                    async with session.get(
                        f'{self.railway_url}{endpoint}',
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        if response.status == 200:
                            try:
                                data = await response.json()
                                print(f"   ✅ {endpoint}: {response.status}")
                                
                                # Mostrar informações relevantes
                                if 'stats' in data:
                                    stats = data['stats']
                                    print(f"      📈 Mensagens processadas: {stats.get('messages_processed', 0)}")
                                    print(f"      🚫 Mensagens bloqueadas: {stats.get('messages_blocked', 0)}")
                                    print(f"      📤 Respostas enviadas: {stats.get('responses_sent', 0)}")
                                elif 'status' in data:
                                    print(f"      🟢 Status: {data.get('status')}")
                                elif 'message' in data:
                                    print(f"      💬 Message: {data.get('message')}")
                            except:
                                # Se não for JSON, mostrar texto
                                response_text = await response.text()
                                print(f"   ✅ {endpoint}: {response.status} - {response_text[:100]}...")
                        else:
                            print(f"   ❌ {endpoint}: {response.status}")
                            
                except Exception as e:
                    print(f"   💥 {endpoint}: {e}")

async def main():
    diagnostic = MessageProcessingDiagnostic()
    
    try:
        await diagnostic.run_diagnostic()
        await diagnostic.test_webhook_status()
        
        print("\n" + "="*60)
        print("🏆 DIAGNÓSTICO CONCLUÍDO")
        print("="*60)
        
    except Exception as e:
        print(f"\n💥 Erro no diagnóstico: {e}")

if __name__ == "__main__":
    asyncio.run(main())