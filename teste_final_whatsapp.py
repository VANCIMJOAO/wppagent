#!/usr/bin/env python3
"""
🚀 Teste Simples WhatsApp Real
"""

import asyncio
import aiohttp
from datetime import datetime

async def teste_simples():
    print(f"📱 Enviando mensagem teste às {datetime.now().strftime('%H:%M:%S')}")
    
    async with aiohttp.ClientSession() as session:
        params = {
            "phone_number": "5516991022255",
            "message": f"✅ TESTE FINAL - Token atualizado! {datetime.now().strftime('%H:%M:%S')}"
        }
        
        async with session.post(
            "https://wppagent-production.up.railway.app/webhook/test-send",
            params=params,
            timeout=10
        ) as response:
            
            result = await response.text()
            print(f"Status: {response.status}")
            print(f"Resultado: {result}")

if __name__ == "__main__":
    asyncio.run(teste_simples())
