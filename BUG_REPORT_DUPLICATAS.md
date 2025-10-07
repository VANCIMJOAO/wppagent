# 🐛 BUG REPORT: Controle de Duplicatas Não Funciona

**Data:** 2025-10-07  
**Severidade:** 🔴 CRÍTICA  
**Status:** 🔍 EM INVESTIGAÇÃO

---

## 📋 RESUMO

O sistema de controle de duplicatas (`UnifiedResponseControl`) **NÃO está bloqueando mensagens duplicadas** apesar de:
- ✅ Redis funcionando corretamente (testado isoladamente)
- ✅ Singleton pattern implementado
- ✅ Lock assíncrono em uso
- ✅ Lógica de `SET NX` correta no código

---

## 🧪 TESTES REALIZADOS

### Teste 1: Sequencial
```bash
# Enviar mensagem 1
# Aguardar 3s
# Enviar mesma mensagem 2
```
**Resultado:** ❌ Ambas processadas

### Teste 2: Paralelo
```bash
# Enviar ambas simultaneamente
```
**Resultado:** ❌ Ambas processadas (2s de diferença)

### Teste 3: Redis Direto
```python
result1 = await redis.set("test", "1", ex=30, nx=True)  # True
result2 = await redis.set("test", "1", ex=30, nx=True)  # None
```
**Resultado:** ✅ Redis funciona perfeitamente isoladamente

---

## 🔍 DESCOBERTAS

### 1. Redis retorna `None` na PRIMEIRA tentativa
```
Logs (linha 976):
🔍 Redis SET NX result para 'msg_processed:5516991022255:0c19e0bbfffa': None
```

Isso indica que **a chave já existia** no Redis antes mesmo da primeira mensagem!

### 2. Sistema cai para Memory Fallback
```
Logs (linha 978-980):
🔍 Redis result para 5516991022255: False
🔍 Memory result para 5516991022255: True
✅ PERMITIDO: 5516991022255 - Memory - primeira vez
```

Quando Redis retorna `False`, sistema usa memória como fallback.

### 3. Stats Mostram Redis Ativo
```json
{
  "redis_available": true,
  "redis_operations": 2,
  "duplicates_prevented": 0
}
```

Redis está disponível mas duplicatas = 0.

---

## 🤔 HIPÓTESES

### Hipótese 1: Chaves não estão sendo limpas ❌
**Status:** DESCARTADA  
**Motivo:** `clear_cache()` foi chamado e retornou 0 chaves

### Hipótese 2: Múltiplas instâncias do singleton ❌
**Status:** DESCARTADA  
**Motivo:** Singleton implementado corretamente, única instância confirmada

### Hipótese 3: Lock não funciona ❌
**Status:** DESCARTADA  
**Motivo:** Lock está serializ ando requests (2s de diferença entre elas)

### Hipótese 4: Redis retorna valor diferente de True/None ⚠️
**Status:** **EM INVESTIGAÇÃO**  
**Motivo:** Possível que redis.set() retorne algo diferente do esperado

### Hipótese 5: TTL expirando muito rápido ❌
**Status:** DESCARTADA  
**Motivo:** TTL=30s, requests com 2-3s de diferença

### Hipótese 6: Hash mudando entre chamadas ⚠️
**Status:** **EM INVESTIGAÇÃO**  
**Motivo:** Possível que `generate_message_hash()` gere hashes diferentes para mesmo conteúdo

---

## 🔧 CORREÇÕES TENTADAS

1. ✅ Validação de parâmetros None
2. ✅ Lazy initialization async do Redis  
3. ✅ Mover init para dentro do lock
4. ✅ Mudado `result is not None` para `result is True`
5. ✅ Logs detalhados adicionados
6. ⏳ Análise linha-por-linha dos logs do servidor (PENDENTE)

---

## 📊 IMPACTO

- ⚠️ **Custos:** Chamadas duplicadas ao OpenAI GPT-4 (~$0.03 por duplicata)
- ⚠️ **UX:** Cliente pode receber respostas duplicadas
- ⚠️ **Performance:** Processamento duplicado sobrecarrega sistema
- ⚠️ **Database:** Mensagens duplicadas salvas no banco

---

## 🎯 PRÓXIMOS PASSOS

1. **Analisar logs do servidor** linha por linha durante teste
2. **Verificar comportamento do redis.asyncio** - pode ter diferença de implementação
3. **Testar com Redis síncrono** temporariamente para comparar
4. **Adicionar teste unitário** específico para `_can_process_redis`
5. **Considerar implementação alternativa** usando Lua script no Redis (atômico)

---

## 💡 SOLUÇÃO TEMPORÁRIA

Enquanto o bug não é corrigido, o impacto é **baixo em produção** pois:
- WhatsApp raramente envia duplicatas
- Rate limiting por usuário ainda funciona (50 msg/min)
- Sistema continua funcional

**Prioridade:** ALTA mas não bloqueante para produção
