# 🛡️ Advanced Webhook Rate Limiting System

## Visão Geral

Sistema avançado de rate limiting para webhooks implementado para proteger a aplicação contra spam, ataques DDoS e uso abusivo dos endpoints de webhook.

## Características Principais

### 🚀 Rate Limiting Escalonado
- **Burst Protection**: Máximo de 50 requisições em 10 segundos
- **Sustained Limiting**: Máximo de 100 requisições por minuto
- **Escalação Automática**: Bloqueios progressivamente mais longos para violadores recorrentes

### 🔍 Detecção de Padrões Suspeitos
- Análise de tamanho de payload (muito pequeno/grande = suspeito)
- Verificação de User-Agent (bots conhecidos são marcados)
- Detecção de requisições idênticas repetitivas
- Sistema de pontuação de suspeita

### ⚡ Performance Otimizada
- Cache local para reduzir latência
- Pipeline Redis para operações em lote
- Fallback gracioso quando Redis não disponível

### 📊 Métricas em Tempo Real
- Contadores por fonte/tipo de webhook
- Histrico de violações
- Níveis de suspeita (Normal, Warning, Critical, Blocked)

## Configurações por Tipo de Webhook

### WhatsApp Business API
```python
WebhookRateConfig(
    burst_limit=50,         # 50 req/10s
    burst_window=10,        # Janela de burst
    sustained_limit=100,    # 100 req/min
    escalation_factor=0.5,  # Escalação moderada
    block_duration=300      # 5 minutos de bloqueio
)
```

### Meta Webhook Generic
```python
WebhookRateConfig(
    burst_limit=30,         # 30 req/10s
    burst_window=10,
    sustained_limit=60,     # 60 req/min
    escalation_factor=0.3,  # Escalação mais agressiva
    block_duration=600      # 10 minutos de bloqueio
)
```

### Default (Outros)
```python
WebhookRateConfig(
    burst_limit=20,         # 20 req/10s
    burst_window=10,
    sustained_limit=40,     # 40 req/min
    escalation_factor=0.2,  # Escalação mais conservadora
    block_duration=900      # 15 minutos de bloqueio
)
```

## Como Usar

### Aplicar Rate Limiting em Endpoint

```python
from app.auth.webhook_rate_limiter import webhook_rate_limit

@router.post("/webhook")
@webhook_rate_limit(webhook_type="whatsapp_business")
async def webhook_endpoint(request: Request):
    # Seu código aqui
    pass
```

### Verificar Status Programaticamente

```python
from app.auth.webhook_rate_limiter import webhook_rate_limiter

allowed, info = await webhook_rate_limiter.check_webhook_rate_limit(
    source_ip="192.168.1.100",
    webhook_type="whatsapp_business",
    user_agent="WhatsApp/2.21.0",
    payload_size=1024
)

if not allowed:
    # Requisição bloqueada
    print(f"Blocked: {info['reason']}")
else:
    # Requisição permitida
    print(f"Allowed: Level {info['level']}")
```

## Endpoints Administrativos

### 📊 Estatísticas Gerais
```
GET /admin/webhook-rate-limit/stats
```

### 🔍 Verificar Status de Fonte Específica
```
GET /admin/webhook-rate-limit/check-source?source_ip=1.2.3.4&webhook_type=whatsapp_business
```

### 🔓 Limpar Bloqueios (Admin Only)
```
POST /admin/webhook-rate-limit/clear-blocks?source_ip=1.2.3.4&webhook_type=whatsapp_business
```

### ⚙️ Ver Configuração Atual
```
GET /admin/webhook-rate-limit/config
```

### 🧪 Testar Sistema
```
GET /admin/webhook-rate-limit/test?source_ip=test&requests=10
```

### 📈 Métricas em Tempo Real
```
GET /admin/webhook-rate-limit/metrics/real-time
```

## Níveis de Rate Limiting

### 🟢 NORMAL
- Sem indicadores de suspeita
- Rate limiting padrão aplicado

### 🟡 WARNING
- 2+ indicadores de suspeita detectados
- Rate limiting um pouco mais restritivo

### 🔴 CRITICAL
- 3+ indicadores de suspeita
- Rate limiting muito restritivo
- Próximo ao bloqueio automático

### ⛔ BLOCKED
- Limites excedidos
- Fonte temporariamente bloqueada
- Duração do bloqueio aumenta com violações recorrentes

## Indicadores de Suspeita

1. **Payload Size**: Muito pequeno (<10 bytes) ou muito grande (>100KB)
2. **User-Agent**: Contém termos como "bot", "crawler", "scanner", etc.
3. **Padrão Repetitivo**: Mais de 20 requisições idênticas em 5 minutos

## Estrutura Redis

### Chaves Utilizadas
```
webhook_rl:{type}:{ip}:burst         # Controle de burst
webhook_rl:{type}:{ip}:sustained     # Controle sustentado
webhook_rl:{type}:{ip}:blocked       # Status de bloqueio
webhook_rl:{type}:{ip}:violations    # Contador de violações
webhook_rl:{type}:{ip}:pattern       # Análise de padrões
webhook_rl:{type}:{ip}:metrics       # Métricas
webhook_rl:{type}:{ip}:info          # Informações adicionais
```

## Monitoramento e Alertas

### Logs Importantes
```python
# Rate limiting aplicado
logger.info("🛡️ Rate limiting info: level=WARNING, config=whatsapp_business")

# Bloqueio automático
logger.warning("Webhook blocked: webhook_rl:whatsapp_business:1.2.3.4, violation: burst_violation, count: 3, duration: 450s")

# Administrador limpou bloqueios
logger.info("Admin user123 cleared webhook blocks for 1.2.3.4:whatsapp_business")
```

### Métricas para Dashboard
- Total de fontes ativas
- Requisições por minuto
- Taxa de bloqueios
- Top sources por volume
- Distribuição de níveis de suspeita

## Troubleshooting

### Problema: Taxa de falsos positivos alta
**Solução**: Ajustar `escalation_factor` para valores menores ou aumentar `sustained_limit`

### Problema: Sistema muito permissivo
**Solução**: Diminuir `burst_limit` e `sustained_limit`, aumentar `escalation_factor`

### Problema: Bloqueios muito longos
**Solução**: Diminuir `block_duration` ou implementar decaimento temporal das violações

### Problema: Performance degradada
**Solução**: Aumentar `_cache_ttl`, implementar sharding do Redis, ou usar Redis Cluster

## Roadmap

### Próximas Funcionalidades
- [ ] Whitelist/Blacklist por IP/User-Agent
- [ ] Machine Learning para detecção de padrões
- [ ] Integração com sistemas externos de threat intelligence
- [ ] Dashboard web para visualização em tempo real
- [ ] Alertas automáticos via Slack/Email
- [ ] Análise geográfica das requisições
- [ ] Rate limiting baseado em conteúdo/intent

### Melhorias de Performance
- [ ] Implementar Redis Cluster
- [ ] Cache distribuído com TTL inteligente
- [ ] Compressão de dados históricos
- [ ] Sharding automático por região

## Segurança

### Dados Sensíveis
- IPs são hashados para logs longos
- Payloads não são armazenados integralmente
- Informações de usuário são anonimizadas

### Backup e Recovery
- Configurações salvas em banco de dados
- Métricas críticas replicadas
- Procedimento de recovery documentado

---

**Implementado em**: Setembro 2025  
**Versão**: 1.0  
**Status**: ✅ Produção Ready
