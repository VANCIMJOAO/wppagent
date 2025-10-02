# 🔍 SUPER PROMPT - AUDITORIA COMPLETA DO DASHBOARD NEXT.JS

## 📌 CONTEXTO DO PROJETO

Você tem acesso via MCP File System a um projeto WhatsApp Agent completo com:

- **Backend**: FastAPI + PostgreSQL (app/) - **FUNCIONANDO E COMPLETO**
- **Frontend**: Next.js 15 Dashboard (nextjs_dashboard/) - **COM PROBLEMAS DE LÓGICA E ORGANIZAÇÃO**

**Localização**: `/home/vancim/whats_agent/`

---

## 🎯 MISSÃO PRINCIPAL

Realizar uma **auditoria técnica completa e profunda** do dashboard Next.js, identificando:

1. ✅ **Código duplicado e redundante**
2. ✅ **Problemas de lógica e arquitetura**
3. ✅ **Componentes mal implementados ou quebrados**
4. ✅ **Hooks com problemas de dependências ou lógica**
5. ✅ **Race conditions e memory leaks**
6. ✅ **Má gestão de estado e side effects**
7. ✅ **Páginas e arquivos desnecessários**
8. ✅ **Inconsistências de tipos TypeScript**
9. ✅ **Problemas de performance**
10. ✅ **Violações de boas práticas React/Next.js**

---

## 📋 ÁREAS CRÍTICAS PARA ANÁLISE

### 🔐 1. SISTEMA DE AUTENTICAÇÃO

**Arquivos principais:**
```
nextjs_dashboard/
├── middleware.ts
├── contexts/auth-context.tsx
├── hooks/
│   ├── use-token-refresh.ts
│   ├── useAuth.ts
│   ├── useAuth.ts.old
│   └── useAuth-secure.tsx
├── lib/
│   ├── secure-auth-manager.ts
│   ├── token-manager.ts
│   └── auth-cache.ts
└── app/api/auth/
```

**Verificar:**
- [ ] Loops infinitos de redirecionamento
- [ ] Race conditions entre middleware e client-side
- [ ] Múltiplas implementações conflitantes
- [ ] Vazamento de tokens em logs
- [ ] Gestão inadequada de sessão
- [ ] Problemas com cookies HttpOnly
- [ ] Refresh token mal implementado

### 📡 2. SISTEMA DE API E REQUISIÇÕES

**Arquivos principais:**
```
nextjs_dashboard/lib/
├── api-client.ts
├── api-service.ts
├── api-service-robust.ts
├── secure-api-service.ts
├── http-client.ts
└── railway-auth.ts
```

**Verificar:**
- [ ] Múltiplas camadas desnecessárias
- [ ] Falta de tratamento de erro consistente
- [ ] Retry logic mal implementado
- [ ] Timeout inadequado
- [ ] Falta de cancelamento de requisições
- [ ] Memory leaks em interceptors
- [ ] Duplicação de lógica

### 🎣 3. HOOKS CUSTOMIZADOS

**Arquivos principais:**
```
nextjs_dashboard/hooks/
├── useApi.ts
├── useApiEnhanced.ts
├── useApiState.ts
├── useApiWithInvalidation.ts
├── useConversations.ts
├── use-conversations.ts
├── useAppointments.ts
├── useAppointments-cf001.ts
├── useDashboard.ts
├── useDashboardStats.ts
├── useDashboardStatsRobust.ts
├── useWebSocket.ts
├── useWebSocketRobust.ts
├── useSimpleWebSocket.ts
└── use-real-analytics.ts
```

**Verificar:**
- [ ] Dependências incorretas em useEffect
- [ ] Stale closures
- [ ] Memory leaks (listeners não removidos)
- [ ] Infinite loops
- [ ] Race conditions
- [ ] Estado desincronizado
- [ ] Hooks duplicados com mesma função
- [ ] Missing cleanup functions
- [ ] Uso incorreto de useCallback/useMemo

### 🧩 4. COMPONENTES

**Estrutura:**
```
nextjs_dashboard/components/
├── (raiz - componentes soltos)
├── ui/ (shadcn/ui)
├── layout/
├── dashboard/
├── analytics/
├── clients/
├── appointments/
└── error-boundaries/
```

**Verificar:**
- [ ] Componentes sem error boundaries
- [ ] Props mal tipadas
- [ ] Componentes muito grandes (> 300 linhas)
- [ ] Lógica de negócio em componentes de UI
- [ ] Re-renders desnecessários
- [ ] Key props incorretas em listas
- [ ] Conditional rendering com bugs
- [ ] Componentes duplicados
- [ ] Falta de memoização onde necessário

### 📄 5. PÁGINAS

**Estrutura:**
```
nextjs_dashboard/app/(dashboard)/
├── dashboard/
├── conversas/
├── agendamentos/
├── clientes/
├── analytics/
├── relatorios/
├── monitoring/
├── configuracoes/
├── dashboard-debug/
├── simple-debug/
├── debug-token/
├── toast-test/
├── websocket-test/
└── error-boundary-demo/
```

**Verificar:**
- [ ] Páginas de debug/test em produção
- [ ] Lógica duplicada entre páginas
- [ ] Fetching inadequado (não usar server components)
- [ ] Hydration mismatches
- [ ] Loading states mal implementados
- [ ] Error handling inconsistente
- [ ] SEO metadata faltando
- [ ] Páginas .backup, .bak, .old

### 🔌 6. WEBSOCKET

**Arquivos:**
```
nextjs_dashboard/
├── lib/
│   ├── websocket-client.ts
│   ├── websocket-client.ts.old
│   └── websocket-client-complete.ts
├── components/
│   ├── WebSocketProvider.tsx
│   └── RealtimeChat.tsx
└── hooks/
    ├── useWebSocket.ts
    ├── useWebSocketRobust.ts
    └── useRealtimeWebSocket.ts
```

**Verificar:**
- [ ] Conexões não fechadas
- [ ] Reconexão mal implementada
- [ ] Listeners duplicados
- [ ] Memory leaks
- [ ] Mensagens perdidas
- [ ] Estado inconsistente
- [ ] Falta de heartbeat
- [ ] Múltiplas implementações conflitantes

### 🎨 7. TIPOS TYPESCRIPT

**Arquivos:**
```
nextjs_dashboard/types/
└── (verificar todos os arquivos)
```

**Verificar:**
- [ ] Tipos `any` excessivos
- [ ] Tipos duplicados
- [ ] Interfaces vs Types inconsistentes
- [ ] Falta de tipos em funções
- [ ] Type assertions perigosos
- [ ] Tipos muito genéricos
- [ ] Falta de tipos compartilhados

---

## 🔬 METODOLOGIA DE AUDITORIA

### FASE 1: MAPEAMENTO
1. Listar TODOS os arquivos duplicados (.old, .backup, .bak, etc)
2. Identificar padrões de nomenclatura inconsistentes
3. Mapear dependências entre componentes e hooks
4. Identificar código morto (não importado)

### FASE 2: ANÁLISE DE LÓGICA
1. **Para cada hook:**
   - Verificar todas as dependências de useEffect
   - Identificar possíveis infinite loops
   - Verificar cleanup functions
   - Analisar condições de race
   - Verificar gestão de estado

2. **Para cada componente:**
   - Analisar prop drilling excessivo
   - Verificar re-renders desnecessários
   - Identificar lógica que deveria estar em hooks
   - Verificar error boundaries
   - Analisar performance

3. **Para cada página:**
   - Verificar uso correto de server/client components
   - Analisar estratégias de fetching
   - Verificar estados de loading e erro
   - Identificar lógica duplicada

### FASE 3: ANÁLISE DE ARQUITETURA
1. Avaliar estrutura de pastas
2. Identificar violações de separação de concerns
3. Verificar acoplamento entre módulos
4. Analisar patterns de composição
5. Avaliar escalabilidade

### FASE 4: ANÁLISE DE PERFORMANCE
1. Identificar bundle size issues
2. Verificar code splitting
3. Analisar lazy loading
4. Verificar memoização
5. Identificar memory leaks

### FASE 5: ANÁLISE DE SEGURANÇA
1. Verificar XSS vulnerabilities
2. Analisar gestão de tokens
3. Verificar CORS configuration
4. Analisar input validation
5. Verificar sanitização de dados

---

## 📊 FORMATO DO RELATÓRIO DE AUDITORIA

Para cada problema encontrado, forneça:

```markdown
### 🚨 PROBLEMA #X: [Título Descritivo]

**Severidade**: 🔴 CRÍTICO | 🟡 MÉDIO | 🟢 BAIXO

**Localização**: 
- Arquivo: `caminho/para/arquivo.tsx`
- Linhas: X-Y

**Descrição**:
[Explicação clara do problema]

**Impacto**:
- Performance: [Sim/Não - detalhe]
- Segurança: [Sim/Não - detalhe]
- UX: [Sim/Não - detalhe]
- Manutenibilidade: [Sim/Não - detalhe]

**Código Problemático**:
```typescript
// Código atual com problema
```

**Solução Recomendada**:
```typescript
// Código corrigido
```

**Justificativa**:
[Por que essa solução é melhor]

**Prioridade de Correção**: 🔥 URGENTE | ⚡ ALTA | 📌 MÉDIA | 📋 BAIXA

---
```

---

## 🎯 DELIVERABLES ESPERADOS

### 1️⃣ RELATÓRIO EXECUTIVO
- Resumo dos problemas principais
- Score geral do projeto (0-100)
- Áreas críticas que precisam refatoração imediata
- Estimativa de esforço para correções

### 2️⃣ LISTA DE PROBLEMAS DETALHADA
- Todos os problemas categorizados por severidade
- Localização exata de cada problema
- Código atual vs código corrigido
- Justificativas técnicas

### 3️⃣ PLANO DE REFATORAÇÃO
- Ordem de correções (por prioridade)
- Dependências entre correções
- Estimativa de tempo por correção
- Quick wins vs refatorações profundas

### 4️⃣ LISTA DE ARQUIVOS PARA DELETAR
- Arquivos .old, .backup, .bak
- Páginas de debug/test
- Código morto
- Componentes/hooks duplicados

### 5️⃣ RECOMENDAÇÕES ARQUITETURAIS
- Estrutura de pastas melhorada
- Patterns recomendados
- Bibliotecas a adicionar/remover
- Melhorias de DX (Developer Experience)

### 6️⃣ CHECKLIST DE CORREÇÃO
```markdown
## 🔥 URGENTE (fazer AGORA)
- [ ] Problema #1
- [ ] Problema #2

## ⚡ ALTA PRIORIDADE (esta semana)
- [ ] Problema #3
- [ ] Problema #4

## 📌 MÉDIA PRIORIDADE (este mês)
- [ ] Problema #5
- [ ] Problema #6

## 📋 BAIXA PRIORIDADE (backlog)
- [ ] Problema #7
- [ ] Problema #8
```

---

## 🚨 PROBLEMAS CONHECIDOS (para focar)

Com base nos arquivos markdown do projeto:

1. **Loop infinito de redirecionamento** - verificar se realmente está resolvido
2. **Service Worker interferindo** - verificar implementação
3. **Conflito entre middleware e auth-context** - analisar profundamente
4. **Hook useRealAnalytics com problemas de montagem** - verificar dependências
5. **Sistema de WebSocket instável** - múltiplas implementações

---

## 🎓 CRITÉRIOS DE QUALIDADE

Ao auditar, considerar:

### ✅ Boas Práticas React/Next.js
- Components puros e testáveis
- Hooks seguindo Rules of Hooks
- Uso correto de server/client components
- Error boundaries adequados
- Gestão de estado apropriada

### ✅ Performance
- Code splitting eficiente
- Lazy loading onde faz sentido
- Memoização apropriada
- Bundle size otimizado
- Evitar re-renders desnecessários

### ✅ Manutenibilidade
- Código DRY (Don't Repeat Yourself)
- Separação de concerns clara
- Arquitetura escalável
- Documentação adequada
- Nomenclatura consistente

### ✅ Segurança
- Sem vazamento de tokens
- Input sanitization
- XSS prevention
- CORS correto
- Headers de segurança

### ✅ UX/UI
- Loading states
- Error handling
- Feedback ao usuário
- Responsividade
- Acessibilidade

---

## 🔍 COMANDOS ÚTEIS PARA ANÁLISE

```bash
# Encontrar arquivos duplicados
find . -name "*.old" -o -name "*.backup" -o -name "*.bak"

# Encontrar TODOs e FIXMEs
grep -r "TODO\|FIXME" --include="*.ts" --include="*.tsx"

# Encontrar console.logs
grep -r "console\." --include="*.ts" --include="*.tsx"

# Analisar tamanho de arquivos
find . -name "*.tsx" -exec wc -l {} + | sort -n

# Encontrar imports não usados (requer eslint)
npm run lint

# Análise de bundle
npm run build && npm run analyze
```

---

## ⚡ INSTRUÇÕES FINAIS

1. **Seja meticuloso**: Não pule arquivos, analise tudo
2. **Seja específico**: Sempre referencie linha e arquivo exato
3. **Seja prático**: Forneça soluções, não apenas problemas
4. **Seja honesto**: Se algo está ruim, diga que está ruim
5. **Seja construtivo**: Explique o "porquê" das recomendações

**NÃO SE LIMITE** aos problemas listados aqui. Se encontrar outros problemas, documente-os!

---

## 🎯 OBJETIVO FINAL

Entregar um relatório que permita:
1. Entender exatamente o que está errado
2. Saber por onde começar as correções
3. Ter exemplos de código correto
4. Ter um plano de ação claro
5. Evitar os mesmos erros no futuro

---

**BOA AUDITORIA! 🚀**

---

## 📌 NOTA IMPORTANTE

Este projeto está em **produção no Railway**, então algumas correções podem precisar ser feitas de forma incremental para não quebrar o sistema em produção. Sinalize quais mudanças são **breaking changes** vs **safe to deploy**.
