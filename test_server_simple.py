#!/usr/bin/env python3
"""
🔧 SERVIDOR DE TESTE SIMPLIFICADO PARA WEBHOOKS
==============================================

Servidor FastAPI mínimo apenas para testar os endpoints de correção do webhook.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import uvicorn
import time
import json
import hashlib
import asyncio

# =======================================
# CONTROLE GLOBAL DE RESPOSTA ÚNICA
# =======================================

GLOBAL_RESPONSE_CONTROL = {
    'active_responses': {},  # user_id -> timestamp
    'processing_locks': {},  # user_id -> asyncio.Lock
    'message_cache': {},     # message_key -> response_data
    'stats': {
        'messages_processed': 0,
        'messages_blocked': 0,
        'responses_sent': 0,
        'duplicates_prevented': 0,
        'errors': 0
    }
}

def get_message_key(user_id: str, content: str) -> str:
    """Gera chave única para mensagem"""
    content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
    timestamp_window = int(time.time() / 10)  # Janela de 10 segundos
    return f"{user_id}_{content_hash}_{timestamp_window}"

async def ensure_single_response(user_id: str, message_content: str) -> bool:
    """Controle rigoroso de resposta única"""
    message_key = get_message_key(user_id, message_content)
    
    # Criar lock global se não existir
    if user_id not in GLOBAL_RESPONSE_CONTROL['processing_locks']:
        GLOBAL_RESPONSE_CONTROL['processing_locks'][user_id] = asyncio.Lock()
    
    # LOCK RIGOROSO
    async with GLOBAL_RESPONSE_CONTROL['processing_locks'][user_id]:
        current_time = time.time()
        
        # 1. Verificação de mensagem já processada
        if message_key in GLOBAL_RESPONSE_CONTROL['message_cache']:
            cache_entry = GLOBAL_RESPONSE_CONTROL['message_cache'][message_key]
            if current_time - cache_entry['timestamp'] < 60:
                GLOBAL_RESPONSE_CONTROL['stats']['messages_blocked'] += 1
                GLOBAL_RESPONSE_CONTROL['stats']['duplicates_prevented'] += 1
                return False
        
        # 2. Verificação de resposta muito recente
        if user_id in GLOBAL_RESPONSE_CONTROL['active_responses']:
            last_response_time = GLOBAL_RESPONSE_CONTROL['active_responses'][user_id]
            if current_time - last_response_time < 8:
                GLOBAL_RESPONSE_CONTROL['stats']['messages_blocked'] += 1
                return False
        
        # 3. Marcar como processando
        GLOBAL_RESPONSE_CONTROL['message_cache'][message_key] = {
            'timestamp': current_time,
            'processing': True,
            'user_id': user_id,
            'blocked_similar': True
        }
        
        GLOBAL_RESPONSE_CONTROL['active_responses'][user_id] = current_time
        GLOBAL_RESPONSE_CONTROL['stats']['messages_processed'] += 1
        
        return True

def mark_response_sent(user_id: str, message_content: str, response: str):
    """Marca que resposta foi enviada"""
    message_key = get_message_key(user_id, message_content)
    
    if message_key in GLOBAL_RESPONSE_CONTROL['message_cache']:
        GLOBAL_RESPONSE_CONTROL['message_cache'][message_key].update({
            'response': response,
            'processing': False,
            'sent_at': time.time()
        })
    
    GLOBAL_RESPONSE_CONTROL['active_responses'][user_id] = time.time()
    GLOBAL_RESPONSE_CONTROL['stats']['responses_sent'] += 1

# =======================================
# APLICAÇÃO FASTAPI SIMPLIFICADA
# =======================================

app = FastAPI(
    title="WhatsApp Agent - Teste de Correções",
    description="API simplificada para testar correções do webhook",
    version="1.0.0-test"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Tracking de início
start_time = time.time()

# =======================================
# ENDPOINTS DE TESTE
# =======================================

@app.get("/")
async def root():
    """Endpoint raiz"""
    return {
        "message": "WhatsApp Agent - Servidor de Teste",
        "status": "running",
        "corrections_active": True,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "uptime": time.time() - start_time
    }

@app.post("/webhook")
async def webhook_test(request: Request):
    """Webhook simulado para teste das correções"""
    try:
        payload = await request.json()
        
        # Simular processamento de mensagem
        if "entry" in payload:
            for entry in payload["entry"]:
                if "changes" in entry:
                    for change in entry["changes"]:
                        if change.get("field") == "messages":
                            await process_test_message(change["value"])
        
        return {"status": "ok"}
        
    except Exception as e:
        GLOBAL_RESPONSE_CONTROL['stats']['errors'] += 1
        return {"status": "error", "error": str(e)}

async def process_test_message(value: dict):
    """Processamento simulado de mensagem"""
    try:
        if "messages" not in value:
            return
        
        for message in value["messages"]:
            user_id = message.get("from", "test_user")
            content = message.get("text", {}).get("body", "test message")
            
            # Aplicar controle de resposta única
            should_process = await ensure_single_response(user_id, content)
            if not should_process:
                print(f"🚫 Mensagem bloqueada: {user_id}")
                continue
            
            print(f"✅ Processando mensagem de {user_id}: {content[:50]}...")
            
            # Simular resposta
            response = "Obrigado pela sua mensagem!"
            mark_response_sent(user_id, content, response)
            
            print(f"📤 Resposta enviada para {user_id}")
            
    except Exception as e:
        GLOBAL_RESPONSE_CONTROL['stats']['errors'] += 1
        print(f"❌ Erro no processamento: {e}")

@app.get("/webhook/stats")
async def get_stats():
    """Estatísticas das correções"""
    try:
        stats = GLOBAL_RESPONSE_CONTROL['stats'].copy()
        
        total_messages = stats['messages_processed']
        if total_messages > 0:
            block_rate = (stats['messages_blocked'] / total_messages) * 100
            response_rate = (stats['responses_sent'] / total_messages) * 100
            expected_responses = total_messages - stats['messages_blocked']
            effectiveness = (stats['responses_sent'] / expected_responses * 100) if expected_responses > 0 else 0
        else:
            block_rate = 0
            response_rate = 0
            effectiveness = 0
        
        return {
            "status": "active",
            "stats": stats,
            "metrics": {
                "block_rate_percent": round(block_rate, 2),
                "response_rate_percent": round(response_rate, 2),
                "effectiveness_percent": round(effectiveness, 2)
            },
            "health": {
                "single_response_working": effectiveness >= 90,
                "duplicate_prevention_working": block_rate >= 5,
                "low_errors": stats['errors'] < 10
            },
            "cache_info": {
                "cached_messages": len(GLOBAL_RESPONSE_CONTROL['message_cache']),
                "active_users": len(GLOBAL_RESPONSE_CONTROL['active_responses']),
                "processing_locks": len(GLOBAL_RESPONSE_CONTROL['processing_locks'])
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {"error": str(e), "timestamp": datetime.now().isoformat()}

@app.get("/webhook/status")
async def webhook_status():
    """Status do webhook corrigido"""
    try:
        current_time = time.time()
        stats = GLOBAL_RESPONSE_CONTROL['stats']
        
        # Calcular efetividade
        total_messages = stats['messages_processed']
        effectiveness = 0
        if total_messages > 0:
            expected_responses = total_messages - stats['messages_blocked']
            effectiveness = (stats['responses_sent'] / expected_responses * 100) if expected_responses > 0 else 0
        
        return {
            "status": "active",
            "corrections_active": True,
            "single_response_system": True,
            "webhook_working": True,
            "effectiveness_percent": round(effectiveness, 2),
            "stats": stats,
            "cache_status": {
                "messages_cached": len(GLOBAL_RESPONSE_CONTROL['message_cache']),
                "active_users": len(GLOBAL_RESPONSE_CONTROL['active_responses']),
                "locks_active": len(GLOBAL_RESPONSE_CONTROL['processing_locks'])
            },
            "timestamp": datetime.now().isoformat(),
            "uptime": current_time - start_time
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/webhook/control")
async def webhook_control():
    """Status do controle de resposta"""
    try:
        stats = GLOBAL_RESPONSE_CONTROL['stats']
        
        total_messages = stats['messages_processed']
        responses_sent = stats['responses_sent']
        blocks = stats['messages_blocked']
        
        control_working = True
        issues = []
        
        if total_messages == 0:
            control_working = False
            issues.append("Nenhuma mensagem processada ainda")
        
        if total_messages > 0:
            expected_responses = total_messages - blocks
            if expected_responses > 0:
                response_ratio = responses_sent / expected_responses
                if response_ratio > 1.1:
                    control_working = False
                    issues.append(f"Múltiplas respostas detectadas: {response_ratio:.2f} por mensagem")
        
        return {
            "status": "active" if control_working else "issues_detected",
            "response_control": control_working,
            "single_response_working": control_working,
            "anti_duplication_active": True,
            "issues": issues,
            "metrics": {
                "total_messages": total_messages,
                "responses_sent": responses_sent,
                "messages_blocked": blocks,
                "duplicates_prevented": stats['duplicates_prevented'],
                "errors": stats['errors']
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.post("/webhook/reset-stats")
async def reset_stats():
    """Reseta estatísticas"""
    try:
        GLOBAL_RESPONSE_CONTROL['stats'] = {
            'messages_processed': 0,
            'messages_blocked': 0,
            'responses_sent': 0,
            'duplicates_prevented': 0,
            'errors': 0
        }
        
        return {
            "status": "stats_reset",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"error": str(e), "timestamp": datetime.now().isoformat()}

# =======================================
# EXECUTAR SERVIDOR
# =======================================

if __name__ == "__main__":
    print("🚀 Iniciando Servidor de Teste Simplificado...")
    print("📍 Host: 0.0.0.0")
    print("🔌 Porta: 8000")
    print("🎯 Foco: Testar correções do webhook")
    print("=" * 50)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )