# WppAgent Dashboard 📊

Dashboard moderno e elegante para gestão de atendimentos WhatsApp. Desenvolvido com Dash e inspirado no design system Anthropic-light.

## ✨ Funcionalidades

### 🏠 **Home - Visão Geral**
- **KPIs em tempo real**: Conversas, usuários únicos, agendamentos, receita
- **Timeline de conversas**: Gráfico de evolução das conversas ao longo do tempo
- **Conversas recentes**: Lista das últimas interações com clientes
- **Distribuição de mensagens**: Análise de mensagens entrada vs. saída
- **Cards informativos**: Métricas de appointments e performance

### 📈 **Relatórios - Análises Detalhadas**
- **Filtros avançados**: Por período, status, períodos rápidos (hoje, semana, mês, etc.)
- **Tabelas com paginação**: Conversas e agendamentos com busca e ordenação
- **Exportação CSV**: Download completo dos dados filtrados
- **Gráficos analíticos**: Timeline, distribuição de status, métricas de performance
- **Abas organizadas**: Separação clara entre conversas e agendamentos

### 👤 **Perfil - Informações do Sistema**
- **Estatísticas do sistema**: Total de usuários, conversas, mensagens
- **Status de integrações**: WhatsApp API, banco de dados, webhooks
- **Atividade recente**: Log das últimas ações do sistema
- **Informações de uso**: Limites, backups, uptime

## 🏗️ Arquitetura

```
dashboard/
├── app.py                    # 🚀 App principal com servidor
├── requirements.txt          # 📦 Dependências Python
├── assets/                   # 🎨 CSS e recursos estáticos
│   ├── theme.css            # Tema principal Anthropic-light
│   ├── sidebar.css          # Estilos da navegação lateral
│   ├── conversations.css    # Animações de conversas
│   └── overrides.css        # Customizações específicas
├── components/              # 🧱 Componentes reutilizáveis
│   ├── sidebar.py          # Navegação lateral com ícones
│   ├── cards.py            # Cards de métricas e gráficos
│   ├── tables.py           # Tabelas com paginação
│   └── nav.py              # Headers e navegação
├── layout/                  # 📄 Layouts das páginas
│   ├── home.py             # Dashboard principal
│   ├── relatorios.py       # Relatórios e análises
│   └── perfil.py           # Perfil e configurações
├── callbacks/               # ⚡ Lógica interativa
│   ├── home_callbacks.py   # Callbacks da home
│   └── relatorios_callbacks.py  # Filtros, paginação, exportação
└── services/                # 🗄️ Acesso a dados
    ├── db.py               # Conexão Railway PostgreSQL
    └── queries.py          # Queries organizadas por contexto
```

## 🗄️ Estrutura do Banco de Dados

Baseado na análise real do `database_analysis_20250822_111259.json`:

- **users** (112 registros): `id`, `wa_id`, `nome`, `telefone`, `email`, `created_at`, `updated_at`
- **conversations** (40 registros): `id`, `user_id`, `status`, `last_message_at`, `created_at`, `updated_at`, `context`, `phone_number`
- **messages** (2066 registros): `id`, `user_id`, `conversation_id`, `direction`, `message_id`, `content`, `message_type`, `raw_payload`, `created_at`
- **appointments** (17 registros): `id`, `user_id`, `business_id`, `service_id`, `date_time`, `end_time`, `status`, `notes`, `duration`, `price`

## ⚙️ Configuração e Instalação

### 1. **Pré-requisitos**
```bash
Python 3.8+
PostgreSQL (Railway)
```

### 2. **Instalação das dependências**
```bash
cd dashboard/
pip install -r requirements.txt
```

### 3. **Configuração do banco de dados**
```bash
# Copie o .env.example para .env
cp ../.env.example .env

# Configure as variáveis de ambiente:
DATABASE_URL=postgresql://user:pass@host:port/database
DEBUG=True
```

### 4. **Executar o dashboard**
```bash
python app.py
```

O dashboard estará disponível em: `http://localhost:8050`

## 📦 Dependências

```
dash>=2.14.0
dash-bootstrap-components>=1.5.0
dash-mantine-components>=0.12.0
dash-iconify>=0.1.2
plotly>=5.15.0
pandas>=2.0.0
psycopg2-binary>=2.9.7
python-dotenv>=1.0.0
```

## 🎨 Design System

### **Paleta de Cores (Anthropic-light inspired)**
- **Primary**: `#262730` (Cinza escuro sofisticado)
- **Background**: `#fafafa` (Cinza muito claro)
- **Surface**: `#ffffff` (Branco puro)
- **Success**: `#10b981` (Verde esmeralda)
- **Warning**: `#f59e0b` (Âmbar)
- **Error**: `#ef4444` (Vermelho coral)
- **Info**: `#3b82f6` (Azul royal)

### **Tipografia**
- **Títulos**: Space Grotesk (Modern sans-serif)
- **Corpo**: Source Sans 3 (Legível e clean)

### **Componentes**
- **Cards**: Sombras suaves, bordas arredondadas (8px)
- **Sidebar**: Fixa, ícones Tabler, hover states
- **Tabelas**: Listras zebradas, ordenação nativa
- **Gráficos**: Plotly com tema customizado

## 🔧 Funcionalidades Técnicas

### **Home Page**
- [x] KPIs dinâmicos baseados em dados reais
- [x] Gráfico de timeline com Plotly
- [x] Lista de conversas recentes com paginação
- [x] Cards de métricas responsivos
- [x] Atualização automática de dados

### **Relatórios**
- [x] Filtros de data com DatePicker
- [x] Filtros de status com Select
- [x] Períodos rápidos (hoje, semana, mês)
- [x] Tabelas com ordenação e busca nativas
- [x] Paginação customizada com controles
- [x] Exportação CSV com encoding UTF-8-SIG
- [x] Abas para conversas e agendamentos
- [x] Gráficos analíticos interativos

### **Perfil**
- [x] Estatísticas do sistema em tempo real
- [x] Status de integrações com indicadores visuais
- [x] Log de atividades recentes
- [x] Cards informativos sobre uso e limites

## 🚀 Performance e Otimizações

- **Queries otimizadas**: Usando PostgreSQL com índices apropriados
- **Paginação eficiente**: Limit/Offset com contagem de registros
- **Cache de componentes**: Dash built-in component caching
- **Lazy loading**: Dados carregados sob demanda
- **Responsive design**: Mobile-first approach

## 🔐 Segurança

- **Queries parametrizadas**: Proteção contra SQL injection
- **Validação de dados**: Sanitização de inputs do usuário
- **Session management**: Dados sensíveis em sessão
- **Error handling**: Tratamento gracioso de erros de banco

## 📊 Métricas Disponíveis

### **Conversas**
- Total de conversas no período
- Conversas ativas/concluídas/pendentes
- Usuários únicos
- Tempo médio de duração
- Taxa de conversão
- Distribuição por status

### **Mensagens**
- Total de mensagens (entrada/saída)
- Tipos de mensagem (texto, imagem, áudio)
- Volume por dia/semana/mês
- Padrões de horário

### **Agendamentos**
- Total de agendamentos
- Status (confirmado, pendente, cancelado)
- Receita total e média
- Serviços mais populares
- Taxa de confirmação

## 🌍 Ambiente de Produção

Para deploy em produção:

1. **Configure as variáveis de ambiente**:
   ```bash
   DEBUG=False
   HOST=0.0.0.0
   PORT=8080
   DATABASE_URL=postgresql://...
   ```

2. **Use um servidor WSGI**:
   ```bash
   pip install gunicorn
   gunicorn app:server -b 0.0.0.0:8080
   ```

3. **Configuração Railway**:
   ```bash
   railway login
   railway init
   railway up
   ```

## 🐛 Troubleshooting

### **Erro de conexão com banco**
```bash
# Verifique a DATABASE_URL
echo $DATABASE_URL

# Teste a conexão
python -c "from services.db import test_connection; test_connection()"
```

### **Componentes não renderizando**
- Verifique se todas as dependências estão instaladas
- Confirme que o `dash-iconify==0.1.2` está na versão correta
- Limpe o cache do navegador

### **Dados não aparecem**
- Verifique se o banco tem dados nas tabelas principais
- Execute o `database_analyzer.py` para verificar a estrutura
- Confira os logs de erro no console

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📝 Changelog

### **v1.0.0** (Atual)
- ✅ Dashboard completo com 3 páginas funcionais
- ✅ Sistema de filtros e paginação
- ✅ Exportação CSV completa
- ✅ Gráficos interativos com Plotly
- ✅ Design system Anthropic-light implementado
- ✅ Queries otimizadas para estrutura real do banco
- ✅ Responsive design para mobile/desktop

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

---

**Desenvolvido com ❤️ para o projeto WppAgent**

*Dashboard moderno para gestão inteligente de atendimentos WhatsApp*