#!/bin/bash

# 🧹 Script de Limpeza Completa da Pasta lib/
# Remove arquivos legados, backups antigos e reorganiza arquivos ativos

echo "🧹 LIMPEZA COMPLETA DA PASTA lib/"
echo "================================="

cd "$(dirname "$0")/.."

# Cores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Contadores
removed_count=0
moved_count=0
kept_count=0

# Função para remover arquivos
remove_files() {
    local pattern=$1
    local description=$2

    echo -e "\n${YELLOW}📂 ${description}${NC}"

    for file in lib/${pattern}; do
        if [ -f "$file" ]; then
            rm -f "$file"
            echo -e "${RED}🗑️  Removido: $(basename "$file")${NC}"
            ((removed_count++))
        fi
    done
}

# Função para mover para pasta archive
move_to_archive() {
    local pattern=$1
    local description=$2

    echo -e "\n${YELLOW}📦 ${description}${NC}"

    # Criar pasta archive se não existir
    mkdir -p lib/archive

    for file in lib/${pattern}; do
        if [ -f "$file" ]; then
            mv "$file" "lib/archive/"
            echo -e "${CYAN}📦 Arquivado: $(basename "$file")${NC}"
            ((moved_count++))
        fi
    done
}

# Função para verificar arquivos ativos
verify_active() {
    local file=$1
    if [ -f "$file" ]; then
        echo -e "${GREEN}✅ Ativo: $(basename "$file")${NC}"
        ((kept_count++))
    fi
}

echo -e "${BLUE}🔍 Analisando arquivos na pasta lib...${NC}"

# 1. REMOVER arquivos deprecated e seus READMEs
remove_files "*.deprecated" "Removendo arquivos deprecated"
remove_files "*.deprecated.README" "Removendo READMEs deprecated"

# 2. REMOVER backups antigos
remove_files "*.backup.*" "Removendo backups antigos"

# 3. MOVER arquivos não-essenciais para archive
move_to_archive "api-client.ts" "Movendo arquivos não-essenciais"
move_to_archive "offline-fetch.ts" "Movendo arquivos offline"
move_to_archive "offline-storage.ts" "Movendo arquivos offline"

# 4. VERIFICAR arquivos ATIVOS essenciais
echo -e "\n${GREEN}📋 ARQUIVOS ATIVOS MANTIDOS:${NC}"
verify_active "lib/api-service-robust.ts"
verify_active "lib/secure-auth-manager.ts"
verify_active "lib/environment-config.ts"
verify_active "lib/debug.ts"
verify_active "lib/api-service.ts"
verify_active "lib/secure-api-service.ts"
verify_active "lib/use-conversation-endpoints.ts"
verify_active "lib/utils.ts"
verify_active "lib/validations.ts"

# 5. ARQUIVOS ESPECIALIZADOS (manter se usados)
echo -e "\n${CYAN}📋 ARQUIVOS ESPECIALIZADOS:${NC}"
verify_active "lib/api-types-extra.ts"
verify_active "lib/api-validators.ts"
verify_active "lib/appointment-normalizer.ts"
verify_active "lib/database-messages.ts"
verify_active "lib/message-normalizer.ts"
verify_active "lib/react-query.ts"

# 6. CRIAR estrutura organizada
echo -e "\n${BLUE}📁 CRIANDO ESTRUTURA ORGANIZADA...${NC}"

# Criar subpastas organizadas
mkdir -p lib/types
mkdir -p lib/services
mkdir -p lib/config
mkdir -p lib/utils-extra

# Mover arquivos para estrutura organizada (se necessário)
if [ -f "lib/api-types-extra.ts" ]; then
    mv lib/api-types-extra.ts lib/types/
    echo -e "${CYAN}📂 Movido: api-types-extra.ts → types/${NC}"
fi

if [ -f "lib/api-validators.ts" ]; then
    mv lib/api-validators.ts lib/utils-extra/
    echo -e "${CYAN}📂 Movido: api-validators.ts → utils-extra/${NC}"
fi

# 7. CRIAR ÍNDICE DA BIBLIOTECA
echo -e "\n${BLUE}📝 CRIANDO ÍNDICE DA BIBLIOTECA...${NC}"

cat > lib/README.md << 'EOF'
# 📚 Biblioteca de Utilitários - WPPAgent Dashboard

## 🚀 Arquivos Principais (Essenciais)

### 🔐 Autenticação & Segurança
- `api-service-robust.ts` - **Serviço principal de API com cookies seguros**
- `secure-auth-manager.ts` - **Gerenciador de autenticação segura**

### ⚙️ Configuração
- `environment-config.ts` - **Configuração por ambiente (dev/staging/prod)**
- `debug.ts` - **Sistema de logging e debug**

### 🔧 Utilitários Core
- `utils.ts` - **Utilitários gerais**
- `validations.ts` - **Validações e schemas**

### 📡 Comunicação
- `use-conversation-endpoints.ts` - **Hook para endpoints de conversação**
- `api-service.ts` - **Serviço de API (fallback)**
- `secure-api-service.ts` - **Serviço de API seguro**

## 📂 Estrutura Organizada

```
lib/
├── 🔐 Principais (usar estes)
│   ├── api-service-robust.ts     # ⭐ API service seguro
│   ├── secure-auth-manager.ts    # ⭐ Autenticação segura
│   ├── environment-config.ts     # ⭐ Configuração ambiente
│   └── debug.ts                  # ⭐ Sistema de logging
│
├── 🛠️ Utilitários
│   ├── utils.ts                  # Helpers gerais
│   ├── validations.ts            # Validações
│   └── use-conversation-endpoints.ts
│
├── 📦 Especializados
│   ├── types/                    # Tipos e interfaces
│   ├── utils-extra/              # Utilitários avançados
│   └── react-query.ts           # Configuração React Query
│
└── 📁 archive/                   # Arquivos arquivados
    └── (arquivos não-essenciais)
```

## ✅ Arquivos Seguros para Usar

1. **api-service-robust.ts** - Principal, com HttpOnly cookies
2. **secure-auth-manager.ts** - Sistema de auth seguro
3. **environment-config.ts** - URLs dinâmicas por ambiente
4. **debug.ts** - Logging sem vulnerabilidades

## ⚠️ Arquivos Arquivados

Arquivos movidos para `archive/` por serem:
- Legados ou deprecated
- Não-essenciais para funcionamento principal
- Mantidos apenas para referência histórica

## 🔄 Como Importar

```typescript
// ✅ CORRETO - Usar arquivos principais
import apiService from './lib/api-service-robust'
import { secureAuth } from './lib/secure-auth-manager'
import { config } from './lib/environment-config'

// ❌ EVITAR - Arquivos deprecated foram removidos
// import { oldAuthService } from './lib/auth-service' // REMOVIDO
```

---
*Última limpeza: $(date)*
EOF

echo -e "${GREEN}📝 Criado: lib/README.md${NC}"

# 8. ESTATÍSTICAS FINAIS
echo -e "\n${GREEN}✅ LIMPEZA CONCLUÍDA!${NC}"
echo "========================="
echo -e "🗑️  Arquivos removidos: ${RED}${removed_count}${NC}"
echo -e "📦 Arquivos arquivados: ${CYAN}${moved_count}${NC}"
echo -e "✅ Arquivos mantidos: ${GREEN}${kept_count}${NC}"

echo -e "\n${GREEN}🎯 PRÓXIMOS PASSOS:${NC}"
echo "1. Revisar lib/README.md para entender estrutura"
echo "2. Verificar se imports ainda funcionam"
echo "3. Remover pasta lib/archive/ se não precisar dos arquivos"
echo "4. Fazer commit das mudanças de limpeza"

echo -e "\n${BLUE}💡 DICA: Execute 'npm run build' para verificar se não há imports quebrados${NC}"
