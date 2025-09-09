"""
🔧 Configuração Redis no Railway
================================

INSTRUÇÕES PARA ATIVAR REDIS NO RAILWAY:

1. 📱 ADICIONAR REDIS VIA DASHBOARD RAILWAY:
   - Acesse: https://railway.app/
   - Vá para seu projeto: wppagent
   - Clique em "+ New Service"
   - Selecione "Database" -> "Redis"
   - Ou use "Add Template" -> "Redis"

2. 🔗 CONFIGURAR VARIÁVEIS DE AMBIENTE:
   Após criar o Redis, o Railway automaticamente criará:    
   - REDIS_URL=redis://default:password@redis-service:6379
   - REDIS_HOST=redis-service
   - REDIS_PORT=6379
   - REDIS_PASSWORD=generated-password

3. 🔄 CONECTAR OS SERVIÇOS:
   - No dashboard, vá em "Connect"
   - Conecte seu app principal com o Redis service
   - Isso permite comunicação interna

4. 💻 COMANDO CLI (ALTERNATIVA):
   Se preferir usar CLI:
   ```bash
   railway login
   railway link [project-id]
   railway add --template redis
   ```

5. 🛠️ CONFIGURAÇÃO NO CÓDIGO:
   O código já está preparado para usar as variáveis:
   - REDIS_URL (prioridade)
   - REDIS_HOST + REDIS_PORT + REDIS_PASSWORD
   - Fallback para localhost (desenvolvimento)

🎯 DEPOIS DE CONFIGURAR:
1. Faça redeploy do app principal
2. Verifique os logs para confirmar conexão Redis
3. Teste os endpoints que usam cache

⚡ BENEFÍCIOS DO REDIS NO RAILWAY:
- Cache distribuído para múltiplas instâncias
- Persistência de dados de sessão
- Rate limiting compartilhado
- Performance otimizada

🔍 VERIFICAR CONFIGURAÇÃO:
- Dashboard Railway -> Services -> Redis
- Logs do Redis service
- Variáveis de ambiente do app
- Conexão entre services

"""

# Este arquivo serve como documentação da configuração
print("📋 Instruções para configurar Redis no Railway")
