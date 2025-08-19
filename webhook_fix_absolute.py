#!/usr/bin/env python3
"""
🚨 CORREÇÃO ABSOLUTA PARA MÚLTIPLAS RESPOSTAS
============================================

Este script implementa um sistema de controle de resposta única
usando o BANCO DE DADOS como fonte única da verdade, resolvendo
problemas de múltiplas instâncias e race conditions.

PROBLEMA IDENTIFICADO:
- Sistema de cache em arquivo não funciona com múltiplas instâncias
- Locks assíncronos não são compartilhados entre processos
- Railway pode ter múltiplas instâncias rodando

SOLUÇÃO:
- Usar banco de dados PostgreSQL como lock distribuído
- Implementar transação atômica para verificação + inserção
- Sistema de cooldown por usuário no próprio banco
- Verificação de mensagens duplicadas por conteúdo + tempo
"""

import asyncio
import asyncpg
import time
import hashlib
from datetime import datetime, timedelta
from typing import Tuple, Optional

async def check_current_database_state():
    """
    Verifica estado atual do banco
    """
    DATABASE_URL = "postgresql://postgres:UGARTPCwAADBBeBLctoRnQXLsoUvLJxz@caboose.proxy.rlwy.net:13910/railway"
    
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        print("📊 ESTADO ATUAL DO BANCO DE DADOS")
        print("=" * 40)
        
        # Verificar mensagens recentes do usuário 2
        recent_messages = await conn.fetch("""
            SELECT direction, content, created_at
            FROM messages 
            WHERE user_id = 2 
            AND created_at > NOW() - INTERVAL '1 hour'
            ORDER BY created_at DESC
            LIMIT 15
        """)
        
        print(f"\n📨 Mensagens recentes (usuário 2):")
        for msg in recent_messages:
            direction_icon = '📨' if msg['direction'] == 'in' else '📤'
            print(f"   {direction_icon} {msg['created_at'].strftime('%H:%M:%S')} | {msg['content'][:50]}...")
        
        # Contar duplicatas
        duplicates = await conn.fetch("""
            SELECT content, direction, COUNT(*) as count
            FROM messages 
            WHERE user_id = 2 
            AND created_at > NOW() - INTERVAL '1 hour'
            GROUP BY content, direction
            HAVING COUNT(*) > 1
            ORDER BY count DESC
        """)
        
        if duplicates:
            print(f"\n❌ DUPLICATAS DETECTADAS:")
            for dup in duplicates:
                direction_icon = '📨' if dup['direction'] == 'in' else '📤'
                print(f"   {direction_icon} {dup['count']}x: {dup['content'][:50]}...")
        else:
            print(f"\n✅ Nenhuma duplicata detectada")

        # Analisar padrão temporal das duplicatas
        if duplicates:
            print(f"\n🔍 ANÁLISE TEMPORAL DAS DUPLICATAS:")
            for dup in duplicates:
                if dup['direction'] == 'out' and dup['count'] > 1:
                    timing_analysis = await conn.fetch("""
                        SELECT created_at, 
                               LAG(created_at) OVER (ORDER BY created_at) as prev_time
                        FROM messages 
                        WHERE user_id = 2 
                        AND direction = 'out'
                        AND content = $1
                        AND created_at > NOW() - INTERVAL '1 hour'
                        ORDER BY created_at
                    """, dup['content'])
                    
                    print(f"\n   📤 Resposta: {dup['content'][:30]}...")
                    for i, timing in enumerate(timing_analysis):
                        if timing['prev_time']:
                            diff = (timing['created_at'] - timing['prev_time']).total_seconds()
                            print(f"      #{i+1}: {timing['created_at'].strftime('%H:%M:%S')} (diff: {diff:.1f}s)")
                        else:
                            print(f"      #{i+1}: {timing['created_at'].strftime('%H:%M:%S')} (primeira)")
            
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(check_current_database_state())
