#!/usr/bin/env python3
"""
Debug da Chave OpenAI - WhatsApp Agent
Script para diagnosticar problemas com a chave da OpenAI
"""

import os
import asyncio
import openai
from app.config import settings

async def debug_openai_key():
    """Debug completo da configuração OpenAI"""
    print("🔍 DEBUG DA CHAVE OPENAI")
    print("=" * 50)
    
    # 1. Verificar variável de ambiente diretamente
    env_key = os.getenv('OPENAI_API_KEY')
    print(f"\n1. Variável de ambiente OPENAI_API_KEY:")
    if env_key:
        print(f"   ✅ Encontrada: {env_key[:20]}...{env_key[-10:]}")
        print(f"   📏 Tamanho: {len(env_key)} caracteres")
        print(f"   🔤 Formato válido: {'✅' if env_key.startswith('sk-') else '❌'}")
    else:
        print(f"   ❌ Não encontrada na variável de ambiente")
    
    # 2. Verificar através do sistema de configuração
    try:
        config_key = settings.openai_api_key
        print(f"\n2. Através do sistema de configuração:")
        if config_key:
            print(f"   ✅ Encontrada: {config_key[:20]}...{config_key[-10:]}")
            print(f"   📏 Tamanho: {len(config_key)} caracteres")
            print(f"   🔤 Formato válido: {'✅' if config_key.startswith('sk-') else '❌'}")
            
            # 3. Comparar se são iguais
            if env_key and config_key:
                print(f"\n3. Comparação:")
                print(f"   🔄 Chaves iguais: {'✅' if env_key == config_key else '❌'}")
        else:
            print(f"   ❌ Não encontrada no sistema de configuração")
    except Exception as e:
        print(f"   ❌ Erro ao acessar configuração: {e}")
    
    # 4. Testar conexão com OpenAI usando cada chave
    for name, key in [("Ambiente", env_key), ("Config", getattr(settings, 'openai_api_key', None))]:
        if key:
            print(f"\n4. Teste OpenAI com chave do {name}:")
            try:
                client = openai.AsyncOpenAI(api_key=key)
                models = await client.models.list()
                print(f"   ✅ Sucesso! {len(models.data)} modelos disponíveis")
                
                # Teste uma requisição simples
                try:
                    response = await client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[{"role": "user", "content": "Teste"}],
                        max_tokens=10
                    )
                    print(f"   ✅ Chat completions funcionando")
                except Exception as chat_e:
                    print(f"   ❌ Erro no chat completions: {chat_e}")
                    
            except Exception as e:
                print(f"   ❌ Erro na conexão: {e}")
    
    # 5. Verificar outras variáveis relacionadas
    print(f"\n5. Outras configurações relacionadas:")
    openai_model = os.getenv('OPENAI_MODEL', 'Não definido')
    print(f"   📦 OPENAI_MODEL: {openai_model}")
    
    max_tokens = os.getenv('MAX_TOKENS', 'Não definido')
    print(f"   🔢 MAX_TOKENS: {max_tokens}")

if __name__ == "__main__":
    asyncio.run(debug_openai_key())
