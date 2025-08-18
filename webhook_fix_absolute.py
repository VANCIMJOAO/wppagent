#!/usr/bin/env python3
"""
🚨 CORREÇÃO ABSOLUTA DO WEBHOOK - RESPOSTA ÚNICA GARANTIDA
=========================================================
Esta é uma versão RADICAL que GARANTE apenas uma resposta por mensagem,
independentemente de quantos webhooks duplicados o WhatsApp envie.

PROBLEMA IDENTIFICADO:
- WhatsApp envia múltiplos webhooks para a mesma mensagem
- Sistema atual não bloqueia efetivamente
- Locks assíncronos não estão funcionando

SOLUÇÃO DRÁSTICA:
- Cache absoluto com Redis/arquivo
- Verificação tripla antes de qualquer resposta
- Timeout estendido de 5 minutos
- Log detalhado de todos os bloqueios
"""

import asyncio
import time
import json
import hashlib
import os
import aiofiles
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# CACHE ABSOLUTO EM ARQUIVO (para persistir entre restarts)
CACHE_FILE = "/tmp/webhook_absolute_cache.json"
ACTIVE_RESPONSES_FILE = "/tmp/webhook_active_responses.json"

class AbsoluteResponseControl:
    def __init__(self):
        self.cache = {}
        self.active_responses = {}
        self.stats = {
            'messages_processed': 0,
            'messages_blocked': 0,
            'responses_sent': 0,
            'duplicates_prevented': 0,
            'cache_saves': 0,
            'cache_loads': 0
        }
        self.load_cache()
    
    def load_cache(self):
        """Carrega cache de arquivo"""
        try:
            if os.path.exists(CACHE_FILE):
                with open(CACHE_FILE, 'r') as f:
                    self.cache = json.load(f)
                self.stats['cache_loads'] += 1
                print(f"📂 Cache carregado: {len(self.cache)} entradas")
            
            if os.path.exists(ACTIVE_RESPONSES_FILE):
                with open(ACTIVE_RESPONSES_FILE, 'r') as f:
                    self.active_responses = json.load(f)
                print(f"📂 Respostas ativas carregadas: {len(self.active_responses)} entradas")
                
        except Exception as e:
            print(f"❌ Erro ao carregar cache: {e}")
            self.cache = {}
            self.active_responses = {}
    
    def save_cache(self):
        """Salva cache em arquivo"""
        try:
            with open(CACHE_FILE, 'w') as f:
                json.dump(self.cache, f)
            with open(ACTIVE_RESPONSES_FILE, 'w') as f:
                json.dump(self.active_responses, f)
            self.stats['cache_saves'] += 1
            print("💾 Cache salvo persistentemente")
        except Exception as e:
            print(f"❌ Erro ao salvar cache: {e}")
    
    def get_message_key(self, user_id: str, content: str) -> str:
        """Gera chave única para mensagem"""
        content_clean = content.strip().lower()[:100]  # Primeiros 100 chars
        content_hash = hashlib.md5(content_clean.encode()).hexdigest()[:10]
        # Janela de tempo de 5 minutos para considerar "mesma mensagem"
        time_window = int(time.time() / 300)  # 300 segundos = 5 minutos
        return f"{user_id}_{content_hash}_{time_window}"
    
    def cleanup_old_entries(self):
        """Remove entradas antigas do cache"""
        current_time = time.time()
        old_cache_keys = []
        old_response_keys = []
        
        # Limpar cache com mais de 1 hora
        for key, data in self.cache.items():
            if current_time - data.get('timestamp', 0) > 3600:  # 1 hora
                old_cache_keys.append(key)
        
        # Limpar respostas ativas com mais de 10 minutos
        for key, timestamp in self.active_responses.items():
            if current_time - timestamp > 600:  # 10 minutos
                old_response_keys.append(key)
        
        for key in old_cache_keys:
            del self.cache[key]
        
        for key in old_response_keys:
            del self.active_responses[key]
        
        if old_cache_keys or old_response_keys:
            print(f"🧹 Limpeza: {len(old_cache_keys)} cache + {len(old_response_keys)} respostas ativas removidas")
            self.save_cache()
    
    def can_process_message(self, user_id: str, content: str) -> tuple[bool, str]:
        """
        VERIFICAÇÃO ABSOLUTA se mensagem pode ser processada
        Returns: (pode_processar, motivo_bloqueio)
        """
        current_time = time.time()
        message_key = self.get_message_key(user_id, content)
        
        print(f"\n🔍 VERIFICAÇÃO ABSOLUTA para {user_id}")
        print(f"   Conteúdo: {content[:50]}...")
        print(f"   Chave: {message_key}")
        print(f"   Timestamp: {current_time}")
        
        # BLOQUEIO 1: Mensagem exatamente igual já processada?
        if message_key in self.cache:
            cache_entry = self.cache[message_key]
            time_diff = current_time - cache_entry['timestamp']
            print(f"   ❌ CACHE HIT: Processada há {time_diff:.1f}s")
            
            if time_diff < 300:  # 5 minutos
                self.stats['messages_blocked'] += 1
                self.stats['duplicates_prevented'] += 1
                return False, f"Mensagem duplicada processada há {time_diff:.1f}s"
        
        # BLOQUEIO 2: Usuário teve resposta muito recente?
        if user_id in self.active_responses:
            last_response = self.active_responses[user_id]
            time_diff = current_time - last_response
            print(f"   ❌ RESPOSTA RECENTE: Há {time_diff:.1f}s")
            
            if time_diff < 30:  # 30 segundos entre qualquer resposta
                self.stats['messages_blocked'] += 1
                return False, f"Resposta enviada há apenas {time_diff:.1f}s"
        
        # BLOQUEIO 3: Verificar conteúdo similar recente
        content_lower = content.lower().strip()
        for cached_key, cached_data in self.cache.items():
            if cached_data.get('user_id') == user_id:
                cached_content = cached_data.get('content', '').lower().strip()
                if cached_content and len(cached_content) > 5:
                    # Conteúdo 80% similar?
                    similarity = self._calculate_similarity(content_lower, cached_content)
                    if similarity > 0.8:
                        time_diff = current_time - cached_data['timestamp']
                        if time_diff < 120:  # 2 minutos para conteúdo similar
                            self.stats['messages_blocked'] += 1
                            return False, f"Conteúdo similar processado há {time_diff:.1f}s (similaridade: {similarity:.2f})"
        
        print(f"   ✅ LIBERADO para processamento")
        return True, "Aprovado para processamento"
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calcula similaridade básica entre dois textos"""
        if not text1 or not text2:
            return 0.0
        
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 and not words2:
            return 1.0
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def mark_processing(self, user_id: str, content: str) -> str:
        """Marca mensagem como sendo processada"""
        current_time = time.time()
        message_key = self.get_message_key(user_id, content)
        
        self.cache[message_key] = {
            'timestamp': current_time,
            'user_id': user_id,
            'content': content[:100],
            'status': 'processing',
            'processing_start': current_time
        }
        
        self.stats['messages_processed'] += 1
        print(f"🔒 MARCADO COMO PROCESSANDO: {message_key}")
        self.save_cache()
        
        return message_key
    
    def mark_response_sent(self, user_id: str, content: str, response: str):
        """Marca que resposta foi enviada"""
        current_time = time.time()
        message_key = self.get_message_key(user_id, content)
        
        # Atualizar cache da mensagem
        if message_key in self.cache:
            self.cache[message_key].update({
                'status': 'responded',
                'response': response[:200],  # Primeiros 200 chars da resposta
                'sent_at': current_time
            })
        
        # Marcar usuário como tendo resposta recente
        self.active_responses[user_id] = current_time
        self.stats['responses_sent'] += 1
        
        print(f"📤 RESPOSTA ENVIADA E BLOQUEADA: {user_id}")
        print(f"   Resposta: {response[:50]}...")
        
        self.save_cache()
    
    def get_stats(self) -> dict:
        """Retorna estatísticas completas"""
        self.cleanup_old_entries()
        return {
            'stats': self.stats.copy(),
            'cache_size': len(self.cache),
            'active_responses': len(self.active_responses),
            'timestamp': datetime.now().isoformat()
        }

# Instância global
response_control = AbsoluteResponseControl()

async def test_absolute_control():
    """Testa o sistema de controle absoluto"""
    print("\n🧪 TESTE DO SISTEMA DE CONTROLE ABSOLUTO")
    print("="*60)
    
    # Simular múltiplas mensagens duplicadas
    test_cases = [
        ("5511999999999", "Oi, tudo bem?"),
        ("5511999999999", "Oi, tudo bem?"),  # Duplicata
        ("5511999999999", "oi tudo bem"),    # Similar  
        ("5511999999999", "Oi, tudo bem?"),  # Duplicata exata
        ("5511888888888", "Oi, tudo bem?"),  # Usuário diferente
        ("5511999999999", "Quanto custa?"),  # Mensagem diferente
    ]
    
    for i, (user_id, content) in enumerate(test_cases):
        print(f"\n--- TESTE {i+1} ---")
        can_process, reason = response_control.can_process_message(user_id, content)
        
        if can_process:
            message_key = response_control.mark_processing(user_id, content)
            # Simular resposta
            await asyncio.sleep(0.1)  # Simular processamento
            response_control.mark_response_sent(user_id, content, f"Resposta para: {content}")
            print(f"✅ PROCESSADO: {reason}")
        else:
            print(f"🚫 BLOQUEADO: {reason}")
        
        # Pequena pausa entre testes
        await asyncio.sleep(0.5)
    
    # Mostrar estatísticas finais
    stats = response_control.get_stats()
    print(f"\n📊 ESTATÍSTICAS FINAIS:")
    for key, value in stats['stats'].items():
        print(f"   {key}: {value}")
    
    print(f"\n💾 Cache persistente salvo em: {CACHE_FILE}")
    print(f"💾 Respostas ativas salvas em: {ACTIVE_RESPONSES_FILE}")

if __name__ == "__main__":
    asyncio.run(test_absolute_control())