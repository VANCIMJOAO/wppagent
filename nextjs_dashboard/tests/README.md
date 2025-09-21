# 🧪 Testes E2E do Dashboard Next.js

Este diretório contém testes end-to-end (E2E) completos para verificar todas as funcionalidades do dashboard Next.js.

## 📋 Conjuntos de Testes

### 1. **Dashboard Completo** (`dashboard-complete.spec.ts`)
Testa todas as 17 páginas principais e suas funcionalidades:
- ✅ Página inicial e redirecionamento
- ✅ Login e autenticação
- ✅ Dashboard principal com métricas
- ✅ Agendamentos (CRUD, filtros, estatísticas)
- ✅ Conversas (interface WhatsApp-like)
- ✅ Clientes (gestão completa)
- ✅ Analytics (gráficos e KPIs)
- ✅ Relatórios (exportação e visualização)
- ✅ Configurações (todas as abas)
- ✅ Perfil (informações e segurança)
- ✅ Monitoramento (status do sistema)
- ✅ Bloqueados (gestão de horários)
- ✅ Suporte (FAQ e tickets)
- ✅ RBAC (gerenciamento de usuários)
- ✅ Reports (exportação de relatórios)
- ✅ Diagnóstico (status do backend)
- ✅ Responsividade (mobile e desktop)
- ✅ PWA (funcionalidades offline)
- ✅ WebSocket (atualizações em tempo real)
- ✅ Error boundaries (tratamento de erros)

### 2. **CRUD Operations** (`crud-operations.spec.ts`)
Testa operações de banco de dados:
- ✅ CRUD de Agendamentos
- ✅ CRUD de Clientes
- ✅ CRUD de Horários Bloqueados
- ✅ CRUD de Usuários RBAC
- ✅ Validação de formulários
- ✅ Paginação e filtros
- ✅ Confirmação de exclusão

### 3. **Funcionalidades em Tempo Real** (`realtime-features.spec.ts`)
Testa funcionalidades de tempo real:
- ✅ WebSocket (conexão e reconexão)
- ✅ Dashboard (atualizações em tempo real)
- ✅ Conversas (chat em tempo real)
- ✅ Agendamentos (notificações)
- ✅ Monitoramento (status em tempo real)
- ✅ Analytics (gráficos em tempo real)
- ✅ Notificações push
- ✅ Sincronização offline/online
- ✅ Cache e performance
- ✅ Múltiplas abas (sincronização)

### 4. **Exportação e Relatórios** (`export-reports.spec.ts`)
Testa funcionalidades de exportação:
- ✅ Exportação CSV (Agendamentos)
- ✅ Exportação Excel (Conversas)
- ✅ Exportação PDF (Dashboard)
- ✅ Relatórios (gráficos interativos)
- ✅ Filtros de período
- ✅ KPIs executivos
- ✅ Funil de conversão
- ✅ Métricas de performance
- ✅ Análise temporal
- ✅ Formatação brasileira
- ✅ Exportação em lote
- ✅ Validação de dados
- ✅ Relatórios automáticos

### 5. **Autenticação e RBAC** (`auth-rbac.spec.ts`)
Testa sistema de autenticação e permissões:
- ✅ Login (formulário e validação)
- ✅ Logout (limpeza de sessão)
- ✅ Proteção de rotas
- ✅ RBAC (gerenciamento de usuários)
- ✅ RBAC (gerenciamento de roles)
- ✅ RBAC (gerenciamento de permissões)
- ✅ RBAC (atribuição de roles)
- ✅ RBAC (controle de acesso)
- ✅ Sessão (expiração e renovação)
- ✅ 2FA (autenticação de dois fatores)
- ✅ Rate limiting (proteção contra ataques)

### 6. **PWA e Funcionalidades Offline** (`pwa-offline.spec.ts`)
Testa funcionalidades PWA e offline:
- ✅ Service Worker (registro e ativação)
- ✅ Manifest (configuração PWA)
- ✅ Ícones PWA (diferentes tamanhos)
- ✅ Funcionalidades offline
- ✅ Cache (armazenamento de dados)
- ✅ Sincronização (dados offline/online)
- ✅ Notificações push
- ✅ Instalação PWA
- ✅ Performance (métricas PWA)
- ✅ Responsividade (diferentes dispositivos)
- ✅ Acessibilidade (navegação por teclado)
- ✅ Acessibilidade (contraste e legibilidade)
- ✅ Error boundaries (tratamento de erros)
- ✅ Loading states (feedback visual)

## 🚀 Como Executar os Testes

### Pré-requisitos
1. **Node.js** (versão 18 ou superior)
2. **Servidor Next.js** rodando em `http://localhost:3000`
3. **Playwright** instalado

### Instalação
```bash
# Instalar dependências
npm install

# Instalar Playwright
npx playwright install
```

### Execução

#### 1. Executar Todos os Testes
```bash
# Usando o script automatizado
node tests/test-runner.js

# Ou usando Playwright diretamente
npx playwright test
```

#### 2. Executar Testes Específicos
```bash
# Dashboard completo
npx playwright test tests/dashboard-complete.spec.ts

# CRUD operations
npx playwright test tests/crud-operations.spec.ts

# Funcionalidades em tempo real
npx playwright test tests/realtime-features.spec.ts

# Exportação e relatórios
npx playwright test tests/export-reports.spec.ts

# Autenticação e RBAC
npx playwright test tests/auth-rbac.spec.ts

# PWA e offline
npx playwright test tests/pwa-offline.spec.ts
```

#### 3. Executar com Diferentes Navegadores
```bash
# Chrome
npx playwright test --project=chromium

# Firefox
npx playwright test --project=firefox

# Safari
npx playwright test --project=webkit

# Mobile Chrome
npx playwright test --project="Mobile Chrome"

# Mobile Safari
npx playwright test --project="Mobile Safari"
```

#### 4. Executar com Interface Gráfica
```bash
# Interface gráfica do Playwright
npx playwright test --ui

# Modo debug
npx playwright test --debug
```

#### 5. Executar com Relatórios
```bash
# Relatório HTML
npx playwright test --reporter=html

# Relatório JSON
npx playwright test --reporter=json

# Relatório JUnit
npx playwright test --reporter=junit
```

## 📊 Configuração dos Testes

### Credenciais de Teste
```javascript
const TEST_CREDENTIALS = {
  username: 'admin',
  password: 'admin123'
};
```

### URLs de Teste
- **Base URL**: `http://localhost:3000`
- **Login**: `/login`
- **Dashboard**: `/dashboard`
- **Agendamentos**: `/agendamentos`
- **Conversas**: `/conversas`
- **Clientes**: `/clientes`
- **Analytics**: `/analytics`
- **Relatórios**: `/relatorios`
- **Configurações**: `/configuracoes`
- **Perfil**: `/perfil`
- **Monitoramento**: `/monitoring`
- **Bloqueados**: `/bloqueados`
- **Suporte**: `/suporte`
- **RBAC**: `/rbac`
- **Reports**: `/reports`
- **Diagnóstico**: `/diagnostic`

## 🔧 Configuração do Playwright

O arquivo `playwright.config.ts` contém:
- **Browsers**: Chrome, Firefox, Safari, Mobile Chrome, Mobile Safari
- **Reporter**: HTML, JSON, JUnit
- **Screenshots**: Apenas em falhas
- **Videos**: Apenas em falhas
- **Trace**: Apenas em retry
- **Timeout**: 120 segundos para servidor
- **Retry**: 2 tentativas em CI

## 📈 Relatórios

### Relatório HTML
Após executar os testes, acesse:
```
playwright-report/index.html
```

### Relatório JSON
```
test-results/results.json
```

### Relatório JUnit
```
test-results/results.xml
```

## 🐛 Debugging

### 1. Modo Debug
```bash
npx playwright test --debug
```

### 2. Screenshots
Screenshots são capturados automaticamente em falhas e salvos em:
```
test-results/
```

### 3. Videos
Videos são gravados em falhas e salvos em:
```
test-results/
```

### 4. Trace
Trace é capturado em retry e pode ser visualizado com:
```bash
npx playwright show-trace test-results/trace.zip
```

## 📝 Estrutura dos Testes

```
tests/
├── README.md                    # Este arquivo
├── test-runner.js              # Script de execução automatizada
├── dashboard-complete.spec.ts  # Testes completos do dashboard
├── crud-operations.spec.ts     # Testes de operações CRUD
├── realtime-features.spec.ts   # Testes de tempo real
├── export-reports.spec.ts      # Testes de exportação
├── auth-rbac.spec.ts          # Testes de autenticação
└── pwa-offline.spec.ts        # Testes de PWA e offline
```

## 🎯 Cobertura de Testes

### Funcionalidades Testadas
- ✅ **17 páginas principais**
- ✅ **100+ funcionalidades**
- ✅ **CRUD completo** em todas as entidades
- ✅ **Tempo real** com WebSocket
- ✅ **Exportação** em múltiplos formatos
- ✅ **Analytics** avançadas
- ✅ **Sistema de permissões** RBAC
- ✅ **Monitoramento** em tempo real
- ✅ **PWA** com funcionalidades offline
- ✅ **Responsividade** em todos os dispositivos
- ✅ **Acessibilidade** e navegação por teclado
- ✅ **Error boundaries** e tratamento de erros
- ✅ **Performance** e métricas PWA

### Browsers Testados
- ✅ **Chrome** (Desktop)
- ✅ **Firefox** (Desktop)
- ✅ **Safari** (Desktop)
- ✅ **Chrome** (Mobile)
- ✅ **Safari** (Mobile)

### Dispositivos Testados
- ✅ **Mobile** (375x667)
- ✅ **Tablet** (768x1024)
- ✅ **Desktop** (1920x1080)

## 🚨 Troubleshooting

### Problemas Comuns

#### 1. Servidor não está rodando
```bash
# Iniciar servidor
npm run dev

# Aguardar servidor iniciar
# Verificar em http://localhost:3000
```

#### 2. Playwright não instalado
```bash
# Instalar Playwright
npx playwright install

# Instalar dependências
npm install @playwright/test
```

#### 3. Testes falhando por timeout
```bash
# Aumentar timeout
npx playwright test --timeout=60000

# Ou modificar playwright.config.ts
```

#### 4. Screenshots não sendo capturados
```bash
# Verificar permissões de escrita
# Verificar espaço em disco
# Verificar configuração do Playwright
```

## 📞 Suporte

Para problemas com os testes:
1. Verificar se o servidor está rodando
2. Verificar se as credenciais estão corretas
3. Verificar se o Playwright está instalado
4. Verificar os logs de erro
5. Executar em modo debug para investigar

## 🎉 Conclusão

Estes testes garantem que todas as funcionalidades do dashboard Next.js estejam funcionando corretamente, proporcionando:
- **Confiabilidade** na aplicação
- **Detecção precoce** de bugs
- **Garantia de qualidade** do código
- **Documentação viva** das funcionalidades
- **Facilidade de manutenção** e evolução
