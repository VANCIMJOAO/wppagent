# 🔒 Correção de Configuração CORS Insegura

## 📋 Problema Identificado

**Tipo:** Configuração CORS Insegura  
**Severidade:** CRÍTICA  
**CVE Relacionado:** CWE-942 (Permissive Cross-domain Policy with Untrusted Domains)  

### ❌ Configuração Vulnerável Encontrada

```bash
# Configuração INSEGURA - Railway
CORS_ORIGINS=["https://wppagent-production-app-production.up.railway.app", "*"]
```

**Problemas:**
1. **Wildcard `*` permite qualquer origem**
2. **Bypass de proteções Same-Origin Policy** 
3. **Exposição a ataques CSRF e XSS**
4. **Vazamento de dados sensíveis**

## ⚠️ Impactos de Segurança

### 🎯 Ataques Possíveis
- **Cross-Site Request Forgery (CSRF)**
- **Cross-Site Scripting (XSS)**
- **Data Exfiltration**
- **Session Hijacking**
- **Credential Theft**

### 📊 Cenários de Exploração
1. **Site malicioso** fazendo requests para sua API
2. **Roubo de tokens** de autenticação
3. **Ações não autorizadas** em nome do usuário
4. **Bypass** de controles de acesso

## ✅ Solução Implementada

### 🛡️ 1. Remoção Completa de Wildcards

**Antes:**
```python
# INSEGURO
allowed_origins = ["*"]
cors_methods = ["*"] 
cors_headers = ["*"]
```

**Depois:**
```python
# SEGURO
ALLOWED_ORIGINS_PRODUCTION = [
    "https://wppagent-production.up.railway.app",
    "https://wppagent-production-app-production.up.railway.app",
    "https://nextjs-dashboard-production.up.railway.app"
]

ALLOWED_ORIGINS_DEVELOPMENT = [
    "http://localhost:3000",
    "http://localhost:3001", 
    "http://127.0.0.1:3000",
    "https://localhost:3000",
    "http://localhost:8501",
    "http://localhost:8000",
    "http://127.0.0.1:8000"
]
```

### 🔧 2. Headers e Métodos Específicos

```python
# Headers permitidos (específicos)
allowed_headers = [
    "Accept",
    "Accept-Language", 
    "Content-Type",
    "Authorization",
    "X-Requested-With",
    "Origin",
    "Cache-Control", 
    "Pragma",
    "X-CSRF-Token"
]

# Métodos permitidos (específicos)
allowed_methods = [
    "GET", "POST", "PUT", "DELETE", 
    "OPTIONS", "HEAD", "PATCH"
]
```

### 🎯 3. Validação Dinâmica de Origens

```python
def validate_origin(origin: str, allowed_origins: List[str]) -> bool:
    """Valida se uma origem está na lista de permitidas"""
    if not origin:
        return False
    
    # Verificação exata
    if origin in allowed_origins:
        return True
    
    # Para desenvolvimento, permitir variações localhost
    if any("localhost" in allowed for allowed in allowed_origins):
        localhost_pattern = r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"
        if re.match(localhost_pattern, origin):
            return True
    
    return False
```

### 🔐 4. Headers CORS Seguros Dinâmicos

```python
def get_cors_headers(origin: str, is_debug: bool = False) -> Dict[str, str]:
    """Gera headers CORS seguros baseados na origem"""
    allowed_origins = ALLOWED_ORIGINS_DEVELOPMENT if is_debug else ALLOWED_ORIGINS_PRODUCTION
    
    if validate_origin(origin, allowed_origins):
        return {
            "Access-Control-Allow-Origin": origin,  # Origem específica
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, HEAD, PATCH",
            "Access-Control-Allow-Headers": "Accept, Accept-Language, Content-Type, Authorization, X-Requested-With, Origin, Cache-Control, Pragma, X-CSRF-Token",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Max-Age": "3600",
        }
    else:
        # Headers restritivos para origens não permitidas
        return {
            "Access-Control-Allow-Origin": "null",
            "Access-Control-Allow-Methods": "OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Credentials": "false",
        }
```

## 📂 Arquivos Modificados

### 🔧 1. `/app/cors_config.py`
- ✅ Removido todos os wildcards `*`
- ✅ Implementada validação dinâmica de origens
- ✅ Headers CORS seguros baseados na origem
- ✅ Logging detalhado de tentativas de acesso

### ⚙️ 2. `/app/config/environment_config.py`
- ✅ Configuração padrão sem wildcards
- ✅ Origens específicas para desenvolvimento e produção
- ✅ Validadores que impedem wildcards

### 📝 3. `.env.example`
- ✅ Exemplos de configuração segura
- ✅ Comentários explicativos sobre segurança
- ✅ Separação clara entre produção e desenvolvimento

## 🧪 Validação e Testes

### 🔍 Endpoints de Teste Seguros

```bash
# Teste com origem válida
curl -X OPTIONS \
  -H "Origin: https://wppagent-production.up.railway.app" \
  https://wppagent-production.up.railway.app/cors/test -v

# Teste com origem inválida (será rejeitado)
curl -X OPTIONS \
  -H "Origin: https://site-malicioso.com" \
  https://wppagent-production.up.railway.app/cors/test -v
```

### 📊 Resposta para Origem Válida
```json
{
  "status": "success",
  "message": "CORS teste realizado com segurança!",
  "origin": "https://wppagent-production.up.railway.app",
  "origin_valid": true,
  "security_note": "CORS configurado SEM wildcards - máxima segurança"
}
```

### 🚫 Resposta para Origem Inválida
```json
{
  "status": "rejected",
  "message": "CORS teste realizado com segurança!",
  "origin": "https://site-malicioso.com",
  "origin_valid": false,
  "security_note": "Origem não permitida - acesso negado"
}
```

## 🎯 Configuração de Produção

### 🌐 Variáveis de Ambiente Seguras

```bash
# PRODUÇÃO - apenas domínios específicos
CORS_ORIGINS=https://wppagent-production.up.railway.app,https://wppagent-production-app-production.up.railway.app,https://nextjs-dashboard-production.up.railway.app

# CORS - Métodos permitidos (específicos)
CORS_METHODS=GET,POST,PUT,DELETE,OPTIONS,HEAD,PATCH

# CORS - Headers permitidos (específicos)  
CORS_HEADERS=Accept,Accept-Language,Content-Type,Authorization,X-Requested-With,Origin,Cache-Control,Pragma,X-CSRF-Token

# CORS - Credenciais
CORS_CREDENTIALS=true
```

### 🔍 Verificação de Segurança

```python
# Logs de segurança
logger.info("🔒 CORS configurado para PRODUÇÃO com origens restritas")
logger.info("🚫 WILDCARDS REMOVIDOS - Configuração segura ativada")
logger.info(f"📋 Origins permitidas: {len(allowed_origins)} origins específicas")
```

## 📈 Melhorias de Segurança

### ✅ Antes vs Depois

| Aspecto | Antes (Inseguro) | Depois (Seguro) |
|---------|------------------|-----------------|
| **Origens** | `["*"]` | Específicas por ambiente |
| **Métodos** | `["*"]` | Lista específica |
| **Headers** | `["*"]` | Lista específica |
| **Validação** | Nenhuma | Dinâmica por origin |
| **Logging** | Básico | Detalhado com segurança |
| **Ambiente** | Igual para todos | Diferenciado dev/prod |

### 🛡️ Proteções Implementadas

1. **📍 Origem Específica**: Cada request valida a origem exata
2. **🔒 Zero Wildcards**: Nenhum `*` em configurações
3. **🎯 Validação Dinâmica**: Headers baseados na origem
4. **📝 Logging Detalhado**: Rastreamento de tentativas de acesso
5. **🌍 Ambiente Diferenciado**: Configs específicas para dev/prod
6. **⚡ Performance**: Cache de preflight com max-age

## 🚀 Próximos Passos

### 🔍 1. Monitoramento
- Alertas para tentativas de origem inválida
- Métricas de requests CORS rejeitados
- Dashboard de segurança CORS

### 🛡️ 2. Endurecimento Adicional
- Rate limiting para endpoints CORS
- Blacklist de origens maliciosas conhecidas
- Headers de segurança adicionais

### 📊 3. Auditoria
- Review periódico de origens permitidas
- Remoção de origens não utilizadas
- Validação de configurações por ambiente

---

**Status:** ✅ Implementado e Testado  
**Data:** 11 de setembro de 2025  
**Impacto:** Eliminação completa da vulnerabilidade CORS  
**Risco Mitigado:** CRÍTICO → MÍNIMO
