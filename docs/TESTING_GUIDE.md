# 🧪 Comprehensive Test Suite - WhatsApp Agent

## 📋 Visão Geral

Este script Python realiza testes completos e abrangentes de todo o sistema WhatsApp Agent, incluindo:

- **Backend FastAPI** - Todas as APIs e funcionalidades
- **Dashboard Streamlit** - Interface administrativa 
- **Banco de dados PostgreSQL** - Integridade e performance
- **Segurança** - Vulnerabilidades e sanitização
- **Performance** - Load testing e recursos
- **Integrações** - APIs externas e serviços

## 🚀 Como Executar

### Método 1: Script Automatizado (Recomendado)
```bash
./run_tests.sh
```

### Método 2: Execução Direta
```bash
# Ativar ambiente virtual
source venv/bin/activate

# Instalar dependências de teste
pip install -r requirements-test.txt

# Executar testes
python comprehensive_test_suite.py
```

## 📊 O que é Testado

### 🗄️ Banco de Dados
- ✅ Análise completa do schema
- ✅ Mapeamento de todas as tabelas
- ✅ Validação de integridade referencial
- ✅ Teste de operações CRUD
- ✅ Verificação de constraints e índices

### 🤖 Bot/Backend (FastAPI)
- ✅ Health checks da API
- ✅ Webhook do WhatsApp
- ✅ Processamento de mensagens:
  - Saudações ("oi", "olá", "bom dia")
  - Agendamentos ("quero agendar")
  - Cancelamentos ("cancelar agendamento")
  - Reagendamentos ("mudar horário")
  - Informações ("preços", "serviços")
  - Mensagens complexas
  - Testes de spam e sanitização

### 📊 Dashboard (Dash)
- ✅ Verificação de disponibilidade
- ✅ Teste de carregamento
- ✅ Validação de componentes

### 🛡️ Segurança
- ✅ SQL Injection em todos os campos
- ✅ XSS (Cross-Site Scripting)
- ✅ Rate limiting
- ✅ Sanitização de dados
- ✅ Validação de entrada

### ⚡ Performance
- ✅ Load testing com usuários simultâneos
- ✅ Tempo de resposta das APIs
- ✅ Uso de CPU e memória
- ✅ Taxa de erro sob carga

### 🔌 Integrações
- ✅ Conectividade com banco PostgreSQL
- ✅ Operações assíncronας
- ✅ Pool de conexões
- ✅ Transações

## 📋 Relatórios Gerados

### 📄 Relatório HTML
- Localização: `test_reports/comprehensive_report_YYYYMMDD_HHMMSS.html`
- Contém:
  - ✅/❌ Status de cada teste
  - 📊 Métricas de performance  
  - 🛡️ Vulnerabilidades encontradas
  - 📈 Gráficos de cobertura
  - 🔧 Recomendações de melhorias
  - 📋 Log detalhado de todos os testes

### 📊 Dados JSON
- Localização: `test_reports/test_data_YYYYMMDD_HHMMSS.json`
- Dados estruturados para análise programática

### 📝 Schema do Banco
- Localização: `test_reports/database_schema.json`
- Mapeamento completo de todas as tabelas, índices e constraints

## ⚙️ Configurações

O script usa as seguintes configurações padrão:

```python
DATABASE_URL = "postgresql://vancimj:os.getenv("DB_PASSWORD", "SECURE_DB_PASSWORD")@localhost:5432/whats_agent"
API_BASE_URL = "http://localhost:8000"
DASHBOARD_URL = "http://localhost:8054"
TIMEOUT = 30  # segundos
CONCURRENT_USERS = 10  # para teste de carga
```

## 📁 Estrutura de Arquivos Criados

```
test_reports/
├── comprehensive_report_20250808_143022.html  # Relatório principal
├── test_data_20250808_143022.json            # Dados estruturados
└── database_schema.json                       # Schema do banco

logs/
└── test_suite.log                            # Log de execução
```

## 🔧 Dependências

### Principais
- `asyncpg` - Conexão assíncrona com PostgreSQL
- `aiohttp` - Requisições HTTP assíncronas
- `psutil` - Monitoramento de sistema

### Opcionais para Testes Avançados
- `pytest` - Framework de testes
- `pytest-asyncio` - Suporte assíncrono para pytest
- `pytest-html` - Relatórios HTML
- `requests` - Requisições HTTP síncronas

## 🎯 Interpretação dos Resultados

### Status dos Testes
- ✅ **PASSED** - Teste passou completamente
- ⚠️ **WARNING** - Teste passou com ressalvas
- ❌ **FAILED** - Teste falhou
- ⏭️ **SKIPPED** - Teste foi pulado

### Métricas de Performance
- **Requests/second**: Deve ser > 10 req/s
- **Error Rate**: Deve ser < 5%
- **CPU Usage**: Monitora uso durante testes
- **Memory Usage**: Monitora uso de memória

### Security Score
- **90-100%**: Excelente segurança
- **70-89%**: Boa segurança com melhorias
- **< 70%**: Requer atenção imediata

## 🚨 Resolução de Problemas

### Erro de Conexão com Banco
```bash
# Verificar se PostgreSQL está rodando
sudo systemctl status postgresql

# Iniciar se necessário
sudo systemctl start postgresql
```

### Erro de Dependências
```bash
# Reinstalar dependências
pip install -r requirements-test.txt
```

### Servidores não Iniciam
```bash
# Verificar se as portas estão livres
netstat -tulpn | grep -E ':8000|:8501'

# Matar processos se necessário
pkill -f uvicorn
pkill -f streamlit
```

## 📈 Exemplo de Execução

```bash
$ ./run_tests.sh

🧪 WhatsApp Agent - Comprehensive Test Suite
=============================================

📦 Verificando dependências de teste...
🚀 Iniciando execução dos testes...

2025-08-08 14:30:22 - INFO - 🚀 Iniciando WhatsApp Agent Test Suite
2025-08-08 14:30:22 - INFO - 🔧 Configurando ambiente de testes...
2025-08-08 14:30:23 - INFO - ✅ Conexão com banco de dados estabelecida
2025-08-08 14:30:23 - INFO - 🚀 Iniciando execução completa dos testes...
2025-08-08 14:30:23 - INFO - 🔍 Executando: Database Schema Analysis
2025-08-08 14:30:24 - INFO - ✅ Database Schema Analysis - 1.23s
...

🎯 TESTE COMPLETO FINALIZADO!
================================
📊 Resumo Final:
- Total de testes: 9
- Testes passaram: 8
- Taxa de sucesso: 88.9%
- Relatório HTML: test_reports/comprehensive_report_20250808_143022.html
- Dados JSON: test_reports/test_data_20250808_143022.json
================================

✅ Testes concluídos!
📋 Verifique os relatórios em: test_reports/
📝 Logs em: logs/test_suite.log
```

## 🤝 Contribuindo

Para adicionar novos testes:

1. Crie uma nova função de teste na classe `WhatsAppAgentTestSuite`
2. Adicione o teste à lista em `run_all_tests()`
3. Retorne um objeto `TestResult` com os resultados

Exemplo:
```python
async def test_nova_funcionalidade(self) -> TestResult:
    # Implementar teste
    return TestResult(
        name="Nova Funcionalidade",
        status='passed',
        duration=0,
        details="Teste executado com sucesso"
    )
```
