#!/usr/bin/env python3
"""
🔧 TESTE LLM DIRETO - Debug Completo
===================================
Testa o serviço LLM diretamente para verificar
se a formatação está sendo processada corretamente
"""

import asyncio
import json
from app.services.llm_advanced import get_advanced_llm_service
from app.utils.logger import get_logger

logger = get_logger(__name__)

async def test_llm_direct():
    print("🔧 TESTE LLM DIRETO - Debug Completo")
    print("=" * 50)
    
    try:
        # 1. Inicializar serviço LLM
        print("1️⃣ Inicializando serviço LLM...")
        llm_service = get_advanced_llm_service()
        print("   ✅ Serviço LLM inicializado")
        
        # 2. Simular conversa
        print("\n2️⃣ Processando mensagem de teste...")
        user_id = "test_user_123"
        conversation_id = "test_conv_456"
        message = "Quais serviços vocês oferecem?"
        
        print(f"   📨 Mensagem: {message}")
        print(f"   👤 Usuário: {user_id}")
        
        # 3. Processar mensagem
        response = await llm_service.process_message(
            user_id=user_id,
            conversation_id=conversation_id,
            message=message
        )
        
        print(f"\n3️⃣ RESPOSTA GERADA:")
        print(f"   🤖 Texto: {response.text}")
        print(f"   📊 Confiança: {response.confidence}")
        print(f"   🔍 Metadata: {response.metadata}")
        
        # 4. Verificar formatação
        print(f"\n4️⃣ ANÁLISE DE FORMATAÇÃO:")
        text = response.text
        formatting_elements = {
            '💰': '💰' in text,
            '⏰': '⏰' in text,
            '📋': '📋' in text,
            'Numeração (1.)': '1.' in text,
            'Negrito (*)': '*' in text,
            'Itálico (_)': '_' in text,
        }
        
        for element, present in formatting_elements.items():
            status = "✅" if present else "❌"
            print(f"   {status} {element}: {present}")
        
        # 5. Calcular score
        total_elements = len(formatting_elements)
        present_elements = sum(formatting_elements.values())
        score = (present_elements / total_elements) * 100
        
        print(f"\n📊 SCORE DE FORMATAÇÃO: {score:.1f}% ({present_elements}/{total_elements})")
        
        if score >= 70:
            print("🎉 FORMATAÇÃO APROVADA!")
        elif score >= 30:
            print("⚠️ FORMATAÇÃO PARCIAL")
        else:
            print("❌ FORMATAÇÃO INSUFICIENTE")
            
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        logger.error(f"Erro no teste LLM: {e}")

if __name__ == "__main__":
    asyncio.run(test_llm_direct())
