# 🔍 Investigação: Loop Infinito de Redirecionamento

## 📋 Contexto do Problema

### **Sintomas Observados:**
```
Navegou para http://localhost:3000/login
Navegou para http://localhost:3000/login
⚠️ ⚠️ Token inválido ou expirado
🔍 🔄 Redirecionando para login devido a token expirado
🔍 Usuário não autenticado
🔍 🔄 Redirecionando para login - usuário não autenticado
Failed to fetch RSC payload for http://localhost:3000/login
TypeError: NetworkError when attempting to fetch resource
```

### **Padrão do Loop:**
1. Usuário acessa `/login`
2. `auth-context.tsx` detecta token inválido/expirado
3. `use-token-refresh.ts` também detecta token inválido
4. Ambos redirecionam para `/login` simultaneamente
5. Loop infinito entre múltiplos redirecionamentos

## 🎯 Objetivo da Investigação

**Identificar e corrigir a causa raiz do loop infinito de redirecionamento entre `/login` e múltiplos componentes de autenticação.**

## 📊 Informações Técnicas Atuais

### **Arquitetura de Autenticação:**
- **Middleware**: `middleware.ts` - Verifica tokens e protege rotas
- **Auth Context**: `contexts/auth-context.tsx` - Gerencia estado de autenticação
- **Token Refresh**: `hooks/use-token-refresh.ts` - Atualiza tokens automaticamente
- **Cookies**: HttpOnly, Secure, SameSite=Strict

### **Fluxo Atual:**
```
1. Usuário acessa /
2. middleware.ts verifica token
3. Se sem token → redireciona para /login
4. auth-context.tsx verifica autenticação
5. use-token-refresh.ts verifica validade
6. Se token inválido → redireciona para /login
7. LOOP INFINITO
```

## 🔍 Pontos de Investigação

### **1. Verificação de Estado de Autenticação**
- [ ] Como o `auth-context.tsx` determina se o usuário está autenticado?
- [ ] Como o `use-token-refresh.ts` verifica a validade do token?
- [ ] Há conflito entre os dois sistemas de verificação?

### **2. Middleware vs Client-Side**
- [ ] O middleware está permitindo acesso a `/login` quando deveria?
- [ ] Há conflito entre verificação server-side (middleware) e client-side (hooks)?

### **3. Redirecionamentos Simultâneos**
- [ ] Quantos componentes estão tentando redirecionar simultaneamente?
- [ ] Há race conditions entre os redirecionamentos?
- [ ] Como prevenir múltiplos redirecionamentos?

### **4. Estado do Token**
- [ ] O token realmente está inválido ou há problema na verificação?
- [ ] A API `/api/auth/status` está funcionando corretamente?
- [ ] Há problema com cookies HttpOnly?

## 🛠️ Plano de Investigação

### **Fase 1: Análise de Logs**
1. Adicionar logs detalhados em cada ponto de verificação
2. Identificar qual componente inicia o redirecionamento
3. Mapear a sequência exata de eventos

### **Fase 2: Isolamento de Componentes**
1. Testar `auth-context.tsx` isoladamente
2. Testar `use-token-refresh.ts` isoladamente
3. Verificar se o problema é em um componente específico

### **Fase 3: Verificação de API**
1. Testar endpoint `/api/auth/status` diretamente
2. Verificar se retorna dados corretos
3. Confirmar se cookies estão sendo enviados

### **Fase 4: Correção**
1. Implementar solução baseada nos achados
2. Adicionar proteções contra redirecionamentos múltiplos
3. Testar solução em ambiente limpo

## 📝 Perguntas Específicas para Investigação

### **Para o Claude investigar:**

1. **Qual é a sequência exata de eventos que causa o loop?**
   - Analisar logs do console
   - Verificar ordem de execução dos hooks
   - Identificar ponto de entrada do loop

2. **Há conflito entre middleware e client-side authentication?**
   - Comparar lógica de verificação
   - Verificar se há inconsistências
   - Identificar qual sistema deveria ter precedência

3. **O token está realmente inválido ou há problema na verificação?**
   - Testar API `/api/auth/status` diretamente
   - Verificar cookies no navegador
   - Confirmar se a verificação está correta

4. **Como prevenir redirecionamentos múltiplos?**
   - Implementar flag de redirecionamento em andamento
   - Adicionar debounce/throttle nos redirecionamentos
   - Centralizar lógica de redirecionamento

5. **Qual é a solução mais elegante?**
   - Refatorar arquitetura de autenticação
   - Simplificar fluxo de verificação
   - Implementar estado global de autenticação

## 🎯 Resultado Esperado

**Solução que elimine o loop infinito mantendo a funcionalidade de autenticação intacta, com redirecionamentos controlados e previsíveis.**

## 📋 Arquivos Principais para Análise

- `middleware.ts` - Verificação server-side
- `contexts/auth-context.tsx` - Estado global de auth
- `hooks/use-token-refresh.ts` - Refresh automático
- `app/page.tsx` - Página raiz
- `app/login/page.tsx` - Página de login
- `app/api/auth/status/route.ts` - API de status

---

**Use este prompt para investigar sistematicamente o problema e propor uma solução definitiva.**
