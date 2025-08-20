# 🧪 Tests - WhatsApp Agent

Esta pasta contém todos os testes do sistema WhatsApp Agent.

## 📁 Estrutura de Testes

### 🚀 Testes Principais
- `run_super_test.py` - Orquestrador principal dos testes
- `super_test_part1.py` - Testes de infraestrutura e database
- `super_test_part2.py` - Testes de integração e WhatsApp

### 🗄️ Testes de Database
- `database_operations_test.py` - Testes de operações básicas do banco
- `hybrid_database_test.py` - Testes híbridos de performance
- `quick_database_test.py` - Testes rápidos de conectividade

## 🏃‍♂️ Como Executar

### Teste Completo
```bash
cd tests/
python run_super_test.py
```

### Testes Individuais
```bash
# Testes de infraestrutura
python super_test_part1.py

# Testes de integração
python super_test_part2.py

# Teste rápido de database
python quick_database_test.py
```

## 📊 Relatórios

Os testes geram relatórios detalhados em formato JSON e logs estruturados para análise de performance e debugging.

## ⚡ Configuração

Certifique-se de que as variáveis de ambiente estão configuradas:
- `DATABASE_URL`
- `REDIS_URL`
- `META_ACCESS_TOKEN`
- `PHONE_NUMBER_ID`
