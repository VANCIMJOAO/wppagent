# 🚀 Debug Deploy - Railway

## Problema Identificado
O healthcheck do Railway está falhando com "service unavailable" após 14 tentativas.

## Mudanças Implementadas

### 1. Dockerfile Otimizado
- ✅ Corrigido healthcheck para usar `/health` endpoint
- ✅ Melhorado comando de startup com logs detalhados
- ✅ Adicionado logs de variáveis de ambiente

### 2. Logs de Debug Adicionados
- ✅ Logs detalhados no `/health` endpoint
- ✅ Logs de startup no `main.py`
- ✅ Logs de startup no `startup_optimized.py`
- ✅ Endpoint `/railway-health` com informações de debug

### 3. Endpoints de Debug Disponíveis
- `/health` - Health check principal com debug info
- `/ping` - Endpoint mais simples
- `/railway-health` - Debug específico para Railway
- `/healthcheck` - Endpoint alternativo
- `/status` - Status básico
- `/ready` - Readiness check
- `/alive` - Liveness check

## Como Testar

### 1. Teste Local
```bash
# Iniciar servidor local
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Em outro terminal, testar
python test_local.py
```

### 2. Teste Manual
```bash
# Testar endpoints
curl http://localhost:8000/health
curl http://localhost:8000/ping
curl http://localhost:8000/railway-health
```

## Deploy no Railway

### 1. Commit das Mudanças
```bash
git add .
git commit -m "fix: Add detailed debugging for Railway deploy healthcheck"
git push origin main
```

### 2. Monitorar Logs
- Verificar logs de build no Railway
- Verificar logs de startup
- Verificar se as variáveis de ambiente estão corretas

### 3. Debugging
Se ainda falhar, verificar:
1. **Logs de startup** - Procurar por erros na inicialização
2. **Variáveis de ambiente** - Verificar se PORT está definido
3. **Healthcheck** - Testar manualmente os endpoints
4. **Dependências** - Verificar se todas as dependências estão instaladas

## Informações de Debug

### Variáveis de Ambiente Esperadas
- `PORT` - Porta do servidor (Railway define automaticamente)
- `RAILWAY_ENVIRONMENT` - Ambiente do Railway
- `RAILWAY_FAST_START` - Modo rápido do Railway
- `PYTHONUNBUFFERED` - Para logs em tempo real

### Endpoints de Health
Todos os endpoints retornam informações de debug incluindo:
- Porta do servidor
- Ambiente Railway
- Versão do Python
- Plataforma
- Diretório de trabalho

## Próximos Passos

1. **Deploy** - Fazer commit e push das mudanças
2. **Monitorar** - Acompanhar logs de build e startup
3. **Testar** - Verificar se os endpoints respondem
4. **Debug** - Se falhar, analisar logs detalhados

## Troubleshooting

### Se o healthcheck ainda falhar:
1. Verificar se o servidor está iniciando corretamente
2. Verificar se a porta está correta
3. Verificar se não há erros de dependências
4. Verificar se o banco de dados está acessível (se necessário)

### Logs Importantes:
- `🚀 LIFESPAN: Iniciando WhatsApp Agent API...`
- `🔍 LIFESPAN: PORT = XXXX`
- `✅ Health check concluído com sucesso`
