# Testes E2E - Fluxos Críticos

## 🎯 Objetivo

Este conjunto de testes E2E valida os fluxos críticos do sistema:
- **CRUD de Agendamentos**: Criar → Editar → Deletar
- **CRUD de Clientes**: Criar → Editar → Deletar  
- **WebSocket**: Notificações em tempo real
- **Edge Cases**: Validações e cenários extremos

## 📁 Estrutura dos Testes

```
tests/
├── crud-appointments-flow.spec.ts    # Fluxo completo de agendamentos
├── crud-clients-flow.spec.ts         # Fluxo completo de clientes
├── websocket-realtime.spec.ts        # WebSocket e tempo real
├── edge-cases-validation.spec.ts     # Edge cases e validações
├── run-e2e-tests.js                  # Script de execução
├── e2e-config.json                   # Configuração dos testes
└── README-E2E-TESTS.md              # Este arquivo
```

## 🚀 Como Executar

### 1. Executar Todos os Testes
```bash
# Usando o script automatizado
node tests/run-e2e-tests.js

# Ou usando Playwright diretamente
npx playwright test
```

### 2. Executar Testes Específicos
```bash
# CRUD de Agendamentos
node tests/run-e2e-tests.js appointments

# CRUD de Clientes
node tests/run-e2e-tests.js clients

# WebSocket e Tempo Real
node tests/run-e2e-tests.js websocket

# Edge Cases
node tests/run-e2e-tests.js edge-cases
```

### 3. Executar por Navegador
```bash
# Todos os navegadores
node tests/run-e2e-tests.js browsers

# Navegador específico
npx playwright test --project=chromium
npx playwright test --project=firefox
npx playwright test --project=webkit
```

### 4. Executar com Relatórios
```bash
# Relatório HTML
npx playwright test --reporter=html

# Relatório JSON
npx playwright test --reporter=json

# Relatório JUnit
npx playwright test --reporter=junit
```

## 📋 Cenários Testados

### 1. CRUD de Agendamentos (`crud-appointments-flow.spec.ts`)

#### ✅ Cenários Principais
- **Criar Agendamento**: Formulário completo com validações
- **Editar Agendamento**: Modificação de dados existentes
- **Deletar Agendamento**: Exclusão com confirmação
- **Atualização Automática**: Lista atualizada após operações

#### ✅ Validações Testadas
- Campos obrigatórios (Cliente, Serviço, Data, Hora)
- Data não pode ser no passado
- Horário deve estar entre 8h e 18h
- Valor não pode ser negativo
- Duração entre 15 minutos e 8 horas

#### ✅ WebSocket
- Notificações em tempo real
- Atualização automática da lista
- Reconexão automática

### 2. CRUD de Clientes (`crud-clients-flow.spec.ts`)

#### ✅ Cenários Principais
- **Criar Cliente**: Formulário com validações
- **Editar Cliente**: Modificação de dados
- **Deletar Cliente**: Exclusão com aviso sobre dados relacionados
- **Atualização Automática**: Lista atualizada após operações

#### ✅ Validações Testadas
- Campos obrigatórios (Nome, Telefone)
- Email deve ter formato válido
- Telefone deve conter apenas caracteres válidos
- Status do cliente (Ativo, Inativo, Novo, VIP)

#### ✅ Dados Relacionados
- Aviso sobre conversas, mensagens e agendamentos
- Confirmação obrigatória para exclusão
- Preservação de histórico

### 3. WebSocket e Tempo Real (`websocket-realtime.spec.ts`)

#### ✅ Conexão WebSocket
- Estabelecimento de conexão
- Indicadores visuais de status
- Reconexão automática

#### ✅ Notificações
- Notificações de criação/edição/exclusão
- Atualização automática de dados
- Sincronização entre abas

#### ✅ Performance
- Múltiplas operações simultâneas
- Dados grandes via WebSocket
- Timeout e tratamento de erros

### 4. Edge Cases (`edge-cases-validation.spec.ts`)

#### ✅ Validações de Formulário
- Campos vazios
- Datas inválidas
- Formatação incorreta
- Limites de caracteres

#### ✅ Cenários Extremos
- Múltiplas operações simultâneas
- Timeout de requisições
- Dados grandes
- Conflitos de horários

#### ✅ Acessibilidade
- Navegação por teclado
- Screen reader
- Mensagens de erro acessíveis

## 🔧 Configuração

### Pré-requisitos
```bash
# Instalar dependências
npm install

# Instalar Playwright
npx playwright install

# Verificar instalação
npx playwright --version
```

### Servidores Necessários
```bash
# Frontend (Next.js)
npm run dev

# Backend (FastAPI)
# Deve estar rodando em http://localhost:8000
```

### Variáveis de Ambiente
```bash
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
BACKEND_URL=http://localhost:8000
```

## 📊 Relatórios

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
Screenshots são capturados automaticamente em falhas:
```
test-results/
```

### 3. Videos
Videos são gravados em falhas:
```
test-results/
```

### 4. Trace
Trace é capturado em retry:
```bash
npx playwright show-trace test-results/trace.zip
```

## 📈 Métricas de Qualidade

### Cobertura de Testes
- ✅ **100% dos fluxos críticos** testados
- ✅ **Validações completas** de formulários
- ✅ **WebSocket** e tempo real
- ✅ **Edge cases** e cenários extremos
- ✅ **Acessibilidade** e navegação por teclado
- ✅ **Performance** e limites
- ✅ **Responsividade** em todos os dispositivos

### Critérios de Sucesso
- ✅ **Taxa de sucesso**: > 95%
- ✅ **Tempo de execução**: < 5 minutos
- ✅ **Cobertura**: 100% dos fluxos críticos
- ✅ **Acessibilidade**: Navegação por teclado funcional
- ✅ **Performance**: Operações completadas em tempo razoável

## 🚨 Troubleshooting

### Problemas Comuns

#### 1. Servidor não está rodando
```bash
# Verificar se Next.js está rodando
curl http://localhost:3000

# Verificar se backend está rodando
curl http://localhost:8000/health
```

#### 2. WebSocket não conecta
```bash
# Verificar se WebSocket está habilitado
# Verificar configurações de CORS
# Verificar se porta 3000 está disponível
```

#### 3. Testes falham por timeout
```bash
# Aumentar timeout no playwright.config.ts
# Verificar se servidor está respondendo rapidamente
# Verificar se não há bloqueios de rede
```

#### 4. Elementos não encontrados
```bash
# Verificar se seletores estão corretos
# Verificar se elementos estão visíveis
# Verificar se há conflitos de CSS
```

## 📝 Manutenção

### Adicionando Novos Testes
1. Criar arquivo `.spec.ts` na pasta `tests/`
2. Seguir padrão dos testes existentes
3. Adicionar ao script `run-e2e-tests.js`
4. Documentar no README

### Atualizando Configurações
1. Editar `e2e-config.json`
2. Atualizar seletores se necessário
3. Testar configurações antes de commit

### Monitoramento Contínuo
1. Executar testes regularmente
2. Monitorar taxa de sucesso
3. Investigar falhas rapidamente
4. Manter documentação atualizada

## 🎯 Próximos Passos

### Melhorias Planejadas
- [ ] Testes de performance mais detalhados
- [ ] Testes de carga com múltiplos usuários
- [ ] Testes de segurança
- [ ] Testes de acessibilidade mais abrangentes
- [ ] Integração com CI/CD
- [ ] Relatórios automatizados

### Expansão de Cobertura
- [ ] Testes de exportação de dados
- [ ] Testes de relatórios
- [ ] Testes de configurações
- [ ] Testes de permissões RBAC
- [ ] Testes de monitoramento



