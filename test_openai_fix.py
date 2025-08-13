#!/usr/bin/env python3
"""
Teste da Correção OpenAI - WhatsApp Agent
Script para testar se a correção da chave OpenAI funcionou
"""

import asyncio
import time
from datetime import datetime

async def test_openai_fix():
    """Testa se a correção da OpenAI funcionou"""
    print("🧪 TESTE DA CORREÇÃO OPENAI")
    print("=" * 50)
    print(f"⏰ Iniciado em: {datetime.now().strftime('%H:%M:%S')}")
    
    try:
        # Importar após deploy
        from app.services.llm_advanced import AdvancedLLMService
        
        print("\n1. Inicializando serviço LLM...")
        llm_service = AdvancedLLMService()
        
        print("2. Testando geração de resposta...")
        response = await llm_service.generate_response(
            message="Olá, este é um teste",
            user_name="Teste",
            context={
                "conversation_id": "test_123",
                "user_id": "test_user"
            }
        )
        
        if response:
            print("✅ SUCESSO! OpenAI está funcionando!")
            print(f"📝 Resposta gerada: {response.get('message', 'Sem mensagem')[:100]}...")
            print(f"🔧 Usando modelo: {response.get('model', 'Não informado')}")
        else:
            print("❌ FALHA: Resposta vazia")
            
    except Exception as e:
        print(f"❌ ERRO: {e}")
        print("💡 O deploy pode ainda estar em andamento. Tente novamente em alguns minutos.")
    
    print(f"\n⏰ Finalizado em: {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    asyncio.run(test_openai_fix())
