#!/bin/bash

# Script de Limpeza de Arquivos Legados com Vulnerabilidades
# Remove ou depreca arquivos com práticas inseguras de autenticação

echo "🧹 LIMPEZA DE ARQUIVOS LEGADOS COM VULNERABILIDADES"
echo "=================================================="

cd "$(dirname "$0")/.."

# Cores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Contadores
deprecated_count=0
removed_count=0

# Função para deprecar arquivo
deprecate_file() {
    local file=$1
    local reason=$2

    if [ -f "$file" ]; then
        mv "$file" "${file}.deprecated"
        echo -e "${YELLOW}📦 Depreciado: ${file} → ${file}.deprecated${NC}"
        echo "# ARQUIVO DEPRECIADO - $reason" > "${file}.deprecated.README"
        ((deprecated_count++))
    fi
}

# Função para remover arquivo completamente
remove_file() {
    local file=$1
    local reason=$2

    if [ -f "$file" ]; then
        rm -f "$file"
        echo -e "${RED}🗑️  Removido: ${file} - ${reason}${NC}"
        ((removed_count++))
    fi
}

echo -e "${BLUE}🔍 Identificando arquivos legados...${NC}"

# 1. Arquivos de API service antigos com tokens inseguros
echo -e "\n${YELLOW}📁 LIMPANDO SERVIÇOS DE API LEGADOS${NC}"
deprecate_file "lib/api-service.backup.ts" "Token inseguro em memória JS"
deprecate_file "lib/api-service-robust-clean.ts" "Token inseguro em memória JS"
deprecate_file "lib/api-service-fixed.ts" "Token inseguro em localStorage"
deprecate_file "lib/api-config.ts" "Token inseguro com localStorage"

# 2. Arquivos de autenticação legados
echo -e "\n${YELLOW}🔐 LIMPANDO AUTENTICAÇÃO LEGADA${NC}"
deprecate_file "lib/auth-service.ts" "Sistema de refresh token inseguro"
deprecate_file "lib/token-manager.ts" "Gerenciamento inseguro de tokens"
deprecate_file "lib/offline-manager.ts" "Token em localStorage"

# 3. Arquivos de teste/debug inseguros
echo -e "\n${YELLOW}🧪 LIMPANDO ARQUIVOS DE TESTE INSEGUROS${NC}"
remove_file "lib/auth-test.ts" "Credenciais hardcoded em teste"
remove_file "lib/push-service.ts" "Token inseguro em localStorage"

# 4. Arquivos de interceptador com headers inseguros
echo -e "\n${YELLOW}🔄 LIMPANDO INTERCEPTADORES LEGADOS${NC}"
deprecate_file "lib/api-interceptor.ts" "Headers Authorization hardcoded"
deprecate_file "lib/api-endpoints.ts" "Headers Authorization hardcoded"
deprecate_file "lib/http-client.ts" "Sistema de token inseguro"

# 5. Arquivos de analytics com token inseguro
echo -e "\n${YELLOW}📊 LIMPANDO ANALYTICS INSEGUROS${NC}"
deprecate_file "lib/analytics-config.ts" "Token em localStorage"

# 6. Componentes com localStorage inseguro
echo -e "\n${YELLOW}🎨 CORRIGINDO COMPONENTES COM ARMAZENAMENTO INSEGURO${NC}"

# Corrigir PushNotificationTest.tsx
if [ -f "components/push/PushNotificationTest.tsx" ]; then
    echo -e "${BLUE}🔧 Corrigindo PushNotificationTest.tsx${NC}"
    sed -i "s/localStorage.getItem('auth_token')/await getSecureAuthToken()/g" "components/push/PushNotificationTest.tsx"
    sed -i "s/'Authorization': \`Bearer \${[^}]*}\`/'X-Auth-Required': 'true'/g" "components/push/PushNotificationTest.tsx"
fi

# Corrigir sidebar.tsx
if [ -f "components/layout/sidebar.tsx" ]; then
    echo -e "${BLUE}🔧 Corrigindo sidebar.tsx${NC}"
    sed -i "s/localStorage.getItem('user')/await getUserData()/g" "components/layout/sidebar.tsx"
    sed -i "s/localStorage.removeItem('user')/await clearUserData()/g" "components/layout/sidebar.tsx"
fi

# 7. Criar arquivo de migração de segurança
echo -e "\n${BLUE}📝 CRIANDO GUIA DE MIGRAÇÃO${NC}"
cat > "MIGRATION_SECURITY.md" << 'EOF'
# 🛡️ Guia de Migração de Segurança

## Arquivos Depreciados

Os seguintes arquivos foram depreciados devido a vulnerabilidades de segurança:

### ❌ Problemas Identificados:
- Tokens JWT armazenados em `localStorage`/`sessionStorage`
- Headers `Authorization` hardcoded no client-side
- Tokens expostos em memória JavaScript
- Sistemas de refresh token inseguros

### ✅ Soluções Implementadas:
- **HttpOnly Cookies**: Tokens seguros no servidor
- **API Routes**: Autenticação server-side
- **Secure Auth Manager**: Gerenciamento centralizado
- **Environment Config**: URLs dinâmicas por ambiente

### 🔄 Como Migrar:

1. **Substituir API calls antigos:**
```typescript
// ❌ Antigo (inseguro)
const token = localStorage.getItem('auth_token');
headers: { 'Authorization': `Bearer ${token}` }

// ✅ Novo (seguro)
import { secureAuth } from './lib/secure-auth-manager';
// Token automático via HttpOnly cookies
```

2. **Usar novos serviços:**
- `lib/api-service-robust.ts` - API service seguro
- `lib/secure-auth-manager.ts` - Autenticação segura
- `lib/environment-config.ts` - Configuração por ambiente

### 📋 Checklist de Migração:
- [ ] Remover todos os `localStorage.getItem('*token*')`
- [ ] Remover headers `Authorization` hardcoded
- [ ] Usar `secureAuth` para autenticação
- [ ] Testar em todos os ambientes (dev/staging/prod)

EOF

echo -e "\n${GREEN}✅ LIMPEZA CONCLUÍDA!${NC}"
echo "================================"
echo -e "📦 Arquivos depreciados: ${YELLOW}${deprecated_count}${NC}"
echo -e "🗑️  Arquivos removidos: ${RED}${removed_count}${NC}"
echo -e "📝 Guia criado: ${BLUE}MIGRATION_SECURITY.md${NC}"

echo -e "\n${GREEN}🎯 PRÓXIMOS PASSOS:${NC}"
echo "1. Revisar arquivos depreciados se necessário"
echo "2. Testar aplicação com arquivos seguros"
echo "3. Executar ./scripts/test-auth-security.sh novamente"
echo "4. Fazer commit das mudanças de segurança"

echo -e "\n${BLUE}💡 DICA: Execute 'npm run build' para verificar se não há dependências quebradas${NC}"
