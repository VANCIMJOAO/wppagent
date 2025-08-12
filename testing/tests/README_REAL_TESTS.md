# 🧪 Testes Reais - WhatsApp Agent

## 📋 Visão Geral

Esta suíte de testes foi desenvolvida para testar o **sistema real** do WhatsApp Agent **SEM MOCKS**. Os testes interagem diretamente com a API rodando, simulando usuários reais enviando mensagens via webhook.

## 🎯 Objetivos

- ✅ **Validar funcionalidade real** do sistema
- ✅ **Testar fluxos completos** end-to-end
- ✅ **Verificar performance** sob carga real
- ✅ **Validar estabilidade** em cenários diversos
- ✅ **Simular usuários reais** com comportamentos variados

## 📂 Estrutura dos Testes

### 📄 Arquivos Principais

- `conftest_real.py` - Configuração dos testes reais
- `test_real_api.py` - Testes de API e webhook reais
- `test_real_e2e.py` - Testes end-to-end de jornadas completas
- `run_real_tests.sh` - Script para executar todos os testes

### 🏷️ Categorias de Teste

#### 🔧 Testes de API (`@pytest.mark.api`)
- Verificação de saúde da API
- Tempo de resposta
- Processamento de webhook
- Mensagens concorrentes

#### 📱 Testes de Webhook (`@pytest.mark.webhook`)
- Processamento de mensagens simples
- Fluxos de saudação
- Tratamento de entradas inválidas
- Mensagens em rajada

#### 💬 Testes de Conversação (`@pytest.mark.conversation`)
- Fluxos de consulta de preços
- Tentativas de agendamento
- Consultas complexas
- Suporte e dúvidas

#### 🎯 Testes End-to-End (`@pytest.mark.e2e_real`)
- Jornadas completas de descoberta
- Agendamentos completos
- Recuperação de clientes insatisfeitos
- Clientes indecisos

#### ⚡ Testes de Performance (`@pytest.mark.performance`)
- Tempo de resposta sob carga
- Conversas sustentadas
- Múltiplos usuários simultâneos
- Limites do sistema

## 🚀 Como Executar

### 📋 Pré-requisitos

1. **API rodando** em `http://localhost:8000`
2. **Python** com dependências instaladas
3. **Banco de dados** configurado
4. **Redis** rodando (se usando cache)

### ⚡ Execução Rápida

```bash
# Executar todos os testes reais
./run_real_tests.sh

# Ou executar com pytest diretamente
pytest tests/test_real_*.py -v
```

### 🎯 Execução Seletiva

```bash
# Apenas testes de API
pytest tests/test_real_api.py -v -m "real and api"

# Apenas testes de webhook
pytest tests/test_real_api.py -v -m "real and webhook"

# Apenas testes end-to-end
pytest tests/test_real_e2e.py -v -m "real and e2e_real"

# Apenas testes de performance
pytest tests/test_real_*.py -v -m "real and performance"

# Pular testes lentos
pytest tests/test_real_*.py -v -m "real and not slow"
```

### 🛠️ Opções Customizadas

```bash
# Usar URL diferente da API
pytest tests/test_real_*.py -v --api-url="http://localhost:3000"

# Usar telefone base diferente
pytest tests/test_real_*.py -v --real-phone="5511888"

# Apenas testes rápidos
pytest tests/test_real_*.py -v --quick-real
```

## 📊 Cenários de Teste

### 🔍 1. Jornada de Descoberta
Cliente descobrindo os serviços da barbearia:
- Perguntas sobre serviços disponíveis
- Consulta de preços
- Informações sobre localização
- Horários de funcionamento

### 📅 2. Jornada de Agendamento
Cliente fazendo agendamento completo:
- Manifestação de interesse
- Escolha de serviço
- Seleção de horário
- Confirmação de dados
- Finalização do agendamento

### 🆘 3. Jornada de Suporte
Cliente buscando suporte:
- Dúvidas sobre agendamento
- Informações sobre localização
- Políticas de cancelamento
- Resolução de problemas

### 🤔 4. Cliente Indeciso
Simulação de cliente realista que:
- Muda de ideia várias vezes
- Faz muitas perguntas
- Hesita nas decisões
- Precisa de reasseguramento

### 😠 5. Cliente Insatisfeito
Recuperação de cliente com problema:
- Reclamação inicial
- Processo de reconciliação
- Reagendamento
- Satisfação final

## 🎭 Cenários Complexos

### 👥 Múltiplos Usuários
- Conversas simultâneas
- Diferentes tipos de cliente
- Cargas concorrentes
- Estabilidade do sistema

### 📚 Conversas Longas
- Clientes muito detalhistas
- Muitas perguntas
- Interações prolongadas
- Teste de limites

### 🔥 Testes de Stress
- Mensagens em rajada
- Entradas inválidas
- Casos extremos
- Recuperação de erros

## 📈 Métricas Coletadas

### ✅ Taxa de Sucesso
- Porcentagem de mensagens processadas com sucesso
- Meta: **≥ 85%** para fluxos normais
- Meta: **≥ 80%** para cenários complexos

### ⏱️ Tempo de Resposta
- Tempo médio de processamento por mensagem
- Meta: **< 5s** para mensagens simples
- Meta: **< 10s** para processamento complexo

### 🔄 Estabilidade
- Capacidade de lidar com entradas inválidas
- Recuperação após erros
- Consistência ao longo do tempo

## 🔧 Configuração Avançada

### 📡 Variáveis de Ambiente

```bash
# URL da API (padrão: http://localhost:8000)
export REAL_API_URL="http://localhost:8000"

# Telefone base para testes (padrão: 5511999)
export REAL_TEST_PHONE="5511999"

# Timeouts customizados
export API_TIMEOUT="30"
export WEBHOOK_TIMEOUT="15"
```

### 🎛️ Configurações de Teste

Edite `conftest_real.py` para personalizar:

```python
# Timeouts
TIMEOUTS = {
    "api_call": 30.0,
    "webhook_processing": 15.0,
    "conversation_flow": 45.0,
}

# Dados de teste
REAL_BUSINESS_DATA = {
    "name": "Sua Barbearia",
    "phone": "11999887766",
    # ... outros dados
}
```

## 📊 Interpretando Resultados

### ✅ Resultado Positivo
```
✅ JORNADA DE AGENDAMENTO COMPLETA
⏱️ Duração: 45.2s
📈 Taxa de sucesso: 95.0%
💬 Mensagens processadas: 18
```

### ❌ Resultado com Problemas
```
❌ Fluxo de preços falhou: 75.0%
⚠️ Taxa abaixo da meta (85%)
🔍 Verifique logs para detalhes
```

### 📋 Relatório Final
```
📊 RELATÓRIO FINAL DE TESTES REAIS
==================================
🧪 Total de testes: 25
✅ Sucessos: 22
❌ Falhas: 3
📈 Taxa de sucesso: 88.0%
⏱️ Tempo médio por teste: 12.50s
🕐 Duração total da sessão: 325.2s
```

## 🐛 Troubleshooting

### ❌ API não está rodando
```bash
# Verificar se a API está rodando
curl http://localhost:8000/health

# Iniciar a API se necessário
python -m uvicorn app.main:app --reload
```

### 🐌 Testes muito lentos
```bash
# Executar apenas testes rápidos
pytest tests/test_real_*.py -v --quick-real

# Pular testes marcados como lentos
pytest tests/test_real_*.py -v -m "not slow"
```

### 📊 Taxa de sucesso baixa
1. **Verificar logs** da API para erros
2. **Conferir configuração** do banco/Redis
3. **Aumentar timeouts** se necessário
4. **Verificar recursos** do sistema

### 🔌 Problemas de conexão
1. **Verificar firewall** local
2. **Confirmar porta** da API (8000)
3. **Testar conectividade** manual
4. **Verificar certificados** se HTTPS

## 💡 Dicas de Uso

### 🎯 Para Desenvolvimento
- Execute testes após mudanças no código
- Use apenas testes rápidos durante desenvolvimento
- Foque em categories específicas

### 🚀 Para Deploy
- Execute suite completa antes do deploy
- Verifique métricas de performance
- Documente resultados

### 🔍 Para Debug
- Use `-v` para output detalhado
- Use `--tb=long` para stack traces completos
- Execute testes individuais para investigar

## 🎉 Conclusão

Esta suíte de testes reais garante que o WhatsApp Agent funciona corretamente em cenários reais, sem dependência de mocks ou simulações. Os testes cobrem desde funcionalidades básicas até cenários complexos e edge cases.

**Objetivo:** Garantir que o sistema está pronto para produção e pode lidar com usuários reais em situações diversas.

---

Para mais informações, consulte os arquivos de teste individuais ou execute:
```bash
pytest tests/test_real_*.py --help
```
