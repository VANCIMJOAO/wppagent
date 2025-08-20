# 🧪 Tests - WhatsApp Agent

Esta pasta contém todos os testes do sistema WhatsApp Agent.

## 📁 Estrutura de Testes

### 🚀 Testes Principais
- `run_super_test.py` - Orquestrador principal dos testes
- `super_test_part1.py` - Testes de infraestrutura e database
- `super_test_part2.py` - Testes de integração e WhatsApp

### 📊 Histórico de Testes
Arquivos de teste adicionais estão disponíveis no diretório `archive/test_history/` para referência histórica e debugging.

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
```

### Testes Históricos
```bash
# Para executar testes específicos do archive
cd archive/test_history/
python database_operations_test.py
python hybrid_database_test.py
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
