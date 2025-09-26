# 📊 Documentação Completa - Dashboard WhatsApp Agent

## 🎯 Visão Geral
Este documento mapeia todas as páginas e funcionalidades do dashboard WhatsApp Agent, incluindo botões, campos, CRUDs e todas as interações disponíveis.

---

## 🔐 **PÁGINA DE LOGIN** (`/login`)

### Funcionalidades:
- **Campo Username**: Input para inserir nome de usuário
- **Campo Senha**: Input com toggle para mostrar/ocultar senha
- **Botão "Entrar"**: Autentica o usuário no sistema
- **Validação**: Campos obrigatórios com feedback visual
- **Estados**: Loading durante autenticação, mensagens de erro

---

## 🏠 **DASHBOARD PRINCIPAL** (`/dashboard`)

### Funcionalidades:
- **Botão "Atualizar"**: Recarrega dados do dashboard com ícone de refresh
- **Botão "Analytics Avançadas"**: Navega para página de analytics
- **Cards de Métricas**:
  - Total de Clientes (com ícone Users)
  - Total de Conversas (com ícone MessageSquare)
  - Total de Agendamentos (com ícone Calendar)
  - Taxa de Conversão (com ícone TrendingUp)
- **Cards de Performance**:
  - Tempo de Resposta (com tendência vs período anterior)
  - Satisfação dos Clientes (com score /5.0)
- **Status do Sistema**: Indicador de conexão com backend
- **Call-to-Action**: Botão para acessar analytics completas
- **Auto-refresh**: Atualização automática de dados
- **Loading States**: Skeletons durante carregamento

---

## 💬 **CONVERSAS** (`/conversas`)

### Funcionalidades:
- **Sidebar de Conversas**:
  - **Campo de Busca**: Filtra conversas por nome, telefone ou última mensagem
  - **Botão Refresh**: Recarrega lista de conversas
  - **Lista de Conversas**: 
    - Avatar com status (ativo, humano, fechado)
    - Nome do cliente
    - Última mensagem
    - Timestamp da última mensagem
    - Contador de mensagens
    - Telefone e status
- **Área de Chat**:
  - **Header da Conversa**: Nome, telefone, status
  - **Área de Mensagens**: 
    - Mensagens recebidas (cinza)
    - Mensagens enviadas (azul)
    - Timestamp de cada mensagem
    - Scroll automático para última mensagem
  - **Input de Mensagem**:
    - Campo de texto para nova mensagem
    - Botão de anexo (desabilitado)
    - Botão de emoji (desabilitado)
    - Botão de envio
    - Envio por Enter
- **Estados**: Loading, erro, conversa vazia
- **Filtros**: Busca em tempo real

---

## 👥 **CLIENTES** (`/clientes`)

### Funcionalidades:
- **Header**:
  - **Botão "Atualizar"**: Recarrega dados dos clientes
  - **Botão "Novo Cliente"**: Abre formulário de criação
- **Cards de Estatísticas**:
  - Total de clientes
  - Clientes ativos
  - Clientes VIP
  - Clientes inativos
- **Filtros**:
  - **Campo de Busca**: Por nome, email, telefone
  - **Select de Status**: Todos, Ativo, VIP, Inativo
  - **Select de Ordenação**: Nome, Data de Cadastro, Última Visita, Consultas
- **Lista de Clientes**:
  - Avatar do cliente
  - Nome e badge de status
  - Email, telefone, WA ID
  - Data de cadastro, última visita, consultas, conversas
  - Observações (se houver)
  - **Botões de Ação**:
    - Ver detalhes (ícone Eye)
    - Editar cliente (ícone Edit)
    - Mais opções (ícone MoreVertical)
- **Formulário Novo Cliente**: Modal com campos para criação
- **Estados**: Loading, erro, lista vazia

---

## 📅 **AGENDAMENTOS** (`/agendamentos`)

### Funcionalidades:
- **Header**:
  - **Status WebSocket**: Indicador de conexão em tempo real
  - **Contador de Eventos**: Eventos recentes recebidos
  - **Botões de Exportação**: CSV, Excel, PDF
  - **Botão "Novo Agendamento"**: Cria novo agendamento
- **Cards de Estatísticas**:
  - Total de agendamentos
  - Agendamentos de hoje
  - Confirmados
  - Pendentes
  - Concluídos
  - Cancelados
- **Tabs de Visualização**:
  - **Lista**: Visualização em lista
  - **Calendário**: Agrupado por data
  - **Hoje**: Apenas agendamentos do dia
- **Filtros**:
  - **Campo de Busca**: Por nome do cliente ou serviço
  - **Select de Status**: Todos, Confirmado, Agendado, Realizado, Cancelado
  - **Select de Data**: Todas, Hoje, Amanhã, Esta Semana
- **Lista de Agendamentos**:
  - Ícone de status colorido
  - Nome do cliente e badge de status
  - Data, hora e serviço
  - Observações
  - **Botões de Ação**:
    - Ver detalhes (ícone Eye)
    - Editar (ícone Edit)
    - Excluir (ícone Trash2)
- **WebSocket**: Atualizações em tempo real com notificações toast
- **Estados**: Loading, erro, lista vazia

---

## 📈 **ANALYTICS** (`/analytics`)

### Funcionalidades:
- **Header**:
  - **Select de Período**: 7 dias, 30 dias, 90 dias, 1 ano
  - **Botão "Atualizar"**: Recarrega dados
  - **Botão "Exportar"**: Exporta relatórios
- **Cards de Métricas**:
  - Receita Total (com tendência)
  - Total de Clientes (com tendência)
  - Agendamentos (com tendência)
  - Taxa de Conversão (com tendência)
  - Ticket Médio (com tendência)
  - Retenção de Clientes (com tendência)
- **Tabs de Análise**:
  - **Visão Geral**: Gráficos de receita e distribuição
  - **Receita**: Análise detalhada de receita
  - **Agendamentos**: Por status e serviço
  - **Clientes**: Retenção e demografia
- **Gráficos**: Placeholders para implementação com bibliotecas
- **Dados Reais**: Conectado ao banco PostgreSQL do Railway
- **Estados**: Loading, erro, dados vazios

---

## ⚙️ **CONFIGURAÇÕES** (`/configuracoes`)

### Funcionalidades:
- **Tabs de Configuração**:
  - **Empresa**: Informações da empresa
  - **Bot & IA**: Configurações do assistente virtual
  - **Horários**: Funcionamento e fuso horário
  - **Notificações**: Preferências de alertas
  - **Segurança**: Configurações de segurança

#### **Tab Empresa**:
- **Campos**:
  - Nome da Empresa
  - Telefone
  - Email
  - Website
  - Descrição
  - Endereço
- **Botão "Salvar Configurações"**: Salva dados da empresa

#### **Tab Bot & IA**:
- **Campos**:
  - Nome do Bot
  - Delay de Resposta (0-10 segundos)
  - Mensagem de Boas-vindas
  - Resposta Padrão
- **Configurações de IA**:
  - **Switch "IA Habilitada"**: Liga/desliga IA
  - Máximo de Tokens (50-500)
  - Criatividade/Temperature (0-1)
- **Botão "Salvar Configurações"**: Salva configurações do bot

#### **Tab Horários**:
- **Dias de Trabalho**: Switches para cada dia da semana
- **Campos de Horário**:
  - Horário de Início
  - Horário de Término
  - Início do Almoço
  - Fim do Almoço
- **Select de Fuso Horário**: São Paulo, Rio Branco, Manaus
- **Botão "Salvar Configurações"**: Salva horários

#### **Tab Notificações**:
- **Switches**:
  - Notificações por Email
  - Notificações SMS
  - Notificações Push
  - Lembretes de Agendamento
  - Alertas de Novas Mensagens
- **Botão "Salvar Configurações"**: Salva preferências

#### **Tab Segurança**:
- **Campos de Senha**:
  - Senha Atual
  - Nova Senha
  - Confirmar Nova Senha
- **Configurações de Sessão**:
  - Timeout da Sessão (minutos)
  - Máximo de Tentativas de Login
- **Switch**: Autenticação de Dois Fatores
- **Botão "Salvar Configurações de Segurança"**: Salva configurações

---

## 📊 **RELATÓRIOS** (`/relatorios`)

### Funcionalidades:
- **Header**:
  - **Botão "Atualizar"**: Recarrega dados
- **Seção de Exportação**:
  - **Botão "CSV"**: Exporta em formato CSV
  - **Botão "Excel"**: Exporta em formato Excel
  - **Botão "JSON"**: Exporta em formato JSON
- **Tabs de Análise**:
  - **Visão Geral**: KPIs e gráficos principais
  - **Funil**: Análise de conversão
  - **Performance**: Métricas de desempenho
  - **Tendências**: Dados temporais
- **Cards de KPIs**:
  - Receita Total (com tendência)
  - Conversas Totais (com tendência)
  - Clientes Ativos (com tendência)
  - Taxa de Conversão (com tendência)
- **Gráficos**: 
  - Receita por Fonte (Pizza)
  - Conversas por Status (Barras)
  - Funil de Conversão (Área)
  - Distribuição de Tempo de Resposta (Barras)
  - Tendências Temporais (Linha)
- **Controles de Configuração**:
  - Select de Métrica (Conversas, Receita, Agendamentos, Clientes)
  - Select de Granularidade (Hora, Dia, Semana, Mês)
- **Estados**: Loading, erro, dados vazios

---

## 🆘 **SUPORTE** (`/suporte`)

### Funcionalidades:
- **Header com Status**:
  - **Indicador de Status**: Sistema operacional/degradado/indisponível
  - **Percentual de Uptime**: Tempo de funcionamento
  - **Botão "Atualizar"**: Recarrega dados
- **Status do Sistema**:
  - **Lista de Serviços**:
    - WhatsApp API (com status e uptime)
    - Banco de Dados (com status e uptime)
    - Cache Redis (com status e uptime)
    - Webhook (com status e uptime)
  - **Métricas do Sistema**:
    - Total de Usuários
    - Total de Conversas
    - Total de Agendamentos
    - Total de Mensagens
- **FAQ (Perguntas Frequentes)**:
  - **Filtros por Categoria**:
    - Geral (ícone HelpCircle)
    - Técnico (ícone Settings)
    - Conta (ícone Users)
    - Cobrança (ícone FileText)
  - **Lista de FAQs**: Pergunta, resposta, data de atualização
- **Contato Rápido**:
  - Email de suporte
  - WhatsApp de suporte
  - Horário de atendimento
- **Formulário de Ticket**:
  - **Campos**:
    - Nome
    - Email
    - Categoria (Bug, Sugestão, Conta, Cobrança, Integração, Outros)
    - Prioridade (Baixa, Média, Alta, Urgente)
    - Assunto
    - Mensagem
  - **Botão "Enviar Ticket"**: Cria novo ticket
- **Estados**: Loading, erro, dados vazios

---

## 👤 **PERFIL** (`/perfil`)

### Funcionalidades:
- **Sidebar de Perfil**:
  - **Avatar**: Com botão de câmera para alterar
  - **Informações Básicas**: Nome, email, cargo
  - **Dados de Contato**: Endereço, data de entrada, última atividade
  - **Estatísticas**:
    - Total de Conversas
    - Total de Mensagens
    - Tempo de Resposta
    - Satisfação do Cliente
- **Tabs de Configuração**:
  - **Informações Pessoais**
  - **Segurança**
  - **Preferências**

#### **Tab Informações Pessoais**:
- **Campos Editáveis**:
  - Nome Completo
  - Email
  - Telefone
  - Empresa
  - Endereço
- **Botão "Editar/Salvar"**: Alterna entre modo visualização e edição

#### **Tab Segurança**:
- **Campos de Senha**:
  - Senha Atual (com toggle show/hide)
  - Nova Senha (com toggle show/hide)
  - Confirmar Nova Senha (com toggle show/hide)
- **Botão "Alterar Senha"**: Valida e altera senha

#### **Tab Preferências**:
- **Switches de Notificação**:
  - Notificações por Email
  - Notificações Push
  - Sons de Notificação
  - Resposta Automática
- **Horário de Trabalho**:
  - **Switch**: Ativar Horário de Trabalho
  - **Campos**: Início e Fim (quando ativado)
- **Estados**: Loading, sucesso, erro

---

## 📊 **MONITORAMENTO** (`/monitoring`)

### Funcionalidades:
- **Header**:
  - **Timestamp**: Última atualização
  - **Botão "Atualizar"**: Recarrega dados
- **Status Geral do Sistema**:
  - **Componentes**:
    - WhatsApp API (ícone de status)
    - Banco de Dados (ícone de status)
    - Cache Redis (ícone de status)
    - Webhook (ícone de status)
  - **Métricas**:
    - Tempo de Resposta (ms)
    - Taxa de Erro (%)
    - Sucesso de Mensagens (%)
    - Uptime (%)
- **Alertas Ativos**:
  - **Lista de Alertas**:
    - Badge de Severidade (Low, Medium, High, Critical)
    - Badge de Tipo
    - Título e Mensagem
    - Timestamp
    - **Botão "Resolver"**: Marca alerta como resolvido
    - **Detalhes Técnicos**: Expandível com dados JSON
  - **Estado Vazio**: Mensagem quando não há alertas
- **Auto-refresh**: Atualização a cada 30 segundos
- **Estados**: Loading, erro, dados vazios

---

## 🚫 **HORÁRIOS BLOQUEADOS** (`/bloqueados`)

### Funcionalidades:
- **Header**:
  - **Contador**: Total de registros
  - **Botão "Atualizar"**: Recarrega dados
- **Cards de Métricas**:
  - Total Bloqueados
  - Recorrentes
  - Únicos
  - Próximos 7 Dias
- **Filtros**:
  - **Campo de Busca**: Por motivo ou observações
  - **Botões de Filtro**:
    - Todos
    - Recorrentes
    - Únicos
- **Tabela de Horários Bloqueados**:
  - **Colunas**:
    - Período (data e horário)
    - Motivo
    - Negócio
    - Tipo (Recorrente/Único + Manual/Automático)
    - Criado por
    - Criado em
  - **Badges**: Status coloridos para tipos
- **Estados**: Loading, erro, lista vazia

---

## 📄 **EXPORTAR RELATÓRIOS** (`/exportar-relatorios`)

### Funcionalidades:
- **Componente Principal**: ReportExportComponent
- **Sidebar Informativa**:
  - **Status do Sistema**:
    - Formatos Disponíveis (3)
    - Tipos de Relatório (3)
    - Status (Online)
  - **Guia Rápido**:
    1. Escolha o Tipo
    2. Selecione o Formato
    3. Configure Filtros
    4. Exportar
  - **Dicas**: Uso de cada formato
  - **Características dos Formatos**:
    - CSV: Arquivo leve, compatível com Excel
    - Excel: Formatação avançada, múltiplas abas
    - PDF: Layout profissional, ideal para impressão
- **Proteção**: Acesso restrito a usuários autenticados
- **Estados**: Loading, erro, acesso negado

---

## 🔧 **COMPONENTES E FUNCIONALIDADES GERAIS**

### **Componentes de UI**:
- **Cards**: Containers com header, content e footer
- **Buttons**: Variações (default, outline, ghost, destructive)
- **Inputs**: Campos de texto com validação
- **Selects**: Dropdowns com opções
- **Switches**: Toggles on/off
- **Badges**: Indicadores de status coloridos
- **Tabs**: Navegação entre seções
- **Alerts**: Mensagens de feedback
- **Skeletons**: Loading states
- **Modals**: Janelas sobrepostas

### **Funcionalidades Globais**:
- **Autenticação**: Sistema de login com JWT
- **Navegação**: Sidebar com links para todas as páginas
- **Responsividade**: Design adaptável para mobile/desktop
- **Estados de Loading**: Skeletons e spinners
- **Tratamento de Erro**: Mensagens de erro amigáveis
- **Validação**: Campos obrigatórios e formatos
- **Feedback Visual**: Toasts, alerts, badges de status
- **Auto-refresh**: Atualização automática de dados
- **WebSocket**: Conexão em tempo real
- **Exportação**: Múltiplos formatos (CSV, Excel, PDF, JSON)

### **Integrações**:
- **Backend API**: Conexão com FastAPI
- **Banco de Dados**: PostgreSQL no Railway
- **WebSocket**: Atualizações em tempo real
- **Autenticação**: JWT tokens
- **Exportação**: Geração de relatórios

---

## 📱 **RESPONSIVIDADE**

### **Breakpoints**:
- **Mobile**: < 768px
- **Tablet**: 768px - 1024px
- **Desktop**: > 1024px

### **Adaptações**:
- **Grids**: Colunas se ajustam automaticamente
- **Sidebars**: Colapsam em mobile
- **Tabelas**: Scroll horizontal em telas pequenas
- **Botões**: Tamanhos adaptáveis
- **Formulários**: Layouts em coluna única em mobile

---

## 🎨 **DESIGN SYSTEM**

### **Cores**:
- **Primária**: Azul (#3B82F6)
- **Secundária**: Verde (#10B981)
- **Acento**: Amarelo (#F59E0B)
- **Perigo**: Vermelho (#EF4444)
- **Aviso**: Laranja (#F97316)
- **Info**: Índigo (#6366F1)
- **Sucesso**: Verde (#22C55E)
- **Muted**: Cinza (#6B7280)

### **Tipografia**:
- **Títulos**: Font-bold, tamanhos variados
- **Corpo**: Font-normal, tamanho base
- **Labels**: Font-medium, tamanho pequeno
- **Captions**: Font-normal, tamanho extra pequeno

### **Espaçamentos**:
- **Padding**: 4, 6, 8, 12, 16, 24px
- **Margin**: 2, 4, 6, 8, 12, 16, 24px
- **Gaps**: 2, 4, 6, 8, 12, 16px

---

## 🔄 **FLUXOS DE DADOS**

### **Autenticação**:
1. Login → JWT Token → Armazenamento Local
2. Requests → Header Authorization → Validação Backend
3. Logout → Limpeza Token → Redirecionamento

### **CRUD Operations**:
1. **Create**: Formulário → Validação → API POST → Feedback
2. **Read**: Component Mount → API GET → Estado Local → Render
3. **Update**: Edição → Validação → API PUT → Atualização Estado
4. **Delete**: Confirmação → API DELETE → Remoção Estado

### **Real-time Updates**:
1. WebSocket Connection → Eventos → Estado Local → UI Update
2. Auto-refresh → Interval → API Call → Estado Local → UI Update

---

## 🚀 **PERFORMANCE**

### **Otimizações**:
- **Lazy Loading**: Componentes carregados sob demanda
- **Memoização**: React.memo para componentes pesados
- **Debounce**: Busca com delay para evitar requests excessivos
- **Pagination**: Listas grandes com paginação
- **Caching**: Dados em cache local quando possível

### **Loading States**:
- **Skeletons**: Placeholders durante carregamento
- **Spinners**: Indicadores de processamento
- **Progressive Loading**: Carregamento gradual de dados

---

## 🔒 **SEGURANÇA**

### **Autenticação**:
- **JWT Tokens**: Autenticação stateless
- **Refresh Tokens**: Renovação automática
- **Protected Routes**: Rotas protegidas por autenticação
- **Role-based Access**: Controle de acesso por função

### **Validação**:
- **Client-side**: Validação imediata de formulários
- **Server-side**: Validação no backend
- **Sanitização**: Limpeza de inputs
- **CSRF Protection**: Proteção contra ataques CSRF

---

## 📊 **MÉTRICAS E MONITORAMENTO**

### **Analytics**:
- **User Interactions**: Tracking de cliques e navegação
- **Performance Metrics**: Tempo de carregamento
- **Error Tracking**: Captura de erros
- **Usage Statistics**: Estatísticas de uso

### **Health Checks**:
- **API Status**: Verificação de saúde da API
- **Database Status**: Status do banco de dados
- **WebSocket Status**: Status da conexão em tempo real
- **System Metrics**: Métricas do sistema

---

## 🎯 **CONCLUSÃO**

O Dashboard WhatsApp Agent é um sistema completo e robusto com:

- **15+ Páginas** com funcionalidades específicas
- **100+ Componentes** interativos
- **CRUD Completo** para todas as entidades
- **Real-time Updates** via WebSocket
- **Exportação** em múltiplos formatos
- **Sistema de Autenticação** seguro
- **Design Responsivo** para todos os dispositivos
- **Tratamento de Erros** abrangente
- **Estados de Loading** em todas as operações
- **Integração Completa** com backend FastAPI

Cada página possui funcionalidades específicas e bem definidas, com botões, campos, filtros, e operações CRUD completas, proporcionando uma experiência de usuário rica e funcional.

---

*Documentação gerada em: 2025-01-24*
*Versão do Sistema: 1.0.0*
*Última Atualização: Análise completa de todas as páginas e funcionalidades*
