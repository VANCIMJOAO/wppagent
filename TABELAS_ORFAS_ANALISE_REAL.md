# 🗄️ ANÁLISE **REAL** DE TABELAS ÓRFÃS NO BANCO DE DADOS

> **Data:** 06/10/2025  
> **Análise:** COMPLETA com dados REAIS do PostgreSQL  
> **Status:** ⚠️ **CRÍTICO - Dados encontrados!**

---

## 🔍 VERIFICAÇÃO REAL NO BANCO DE DADOS

### **✅ Todas as 6 tabelas EXISTEM no banco:**

| Tabela | Registros | Status | Uso no Código |
|--------|-----------|--------|---------------|
| `login_attempts` | **0** | 🟢 Vazia | ❌ Nunca usado |
| `user_sessions` | **0** | 🟢 Vazia | ❌ Nunca usado |
| `business_hours` | **14** | 🔴 COM DADOS | ❌ Nunca usado |
| `business_policies` | **3** | 🔴 COM DADOS | ❌ Nunca usado |
| `payment_methods` | **4** | 🔴 COM DADOS | ❌ Nunca usado |
| `auth_users` | **4** | 🔴 COM DADOS | ❌ Nunca usado |

---

## 📊 DETALHES REAIS DAS TABELAS

### **1. `login_attempts` - 0 registros** 🟢

```
Status: VAZIA - nunca foi usada
Definição: app/models/database.py:685-701
Uso no código: 0 referências
```

**Conclusão:** Seguro remover (vazia)

---

### **2. `user_sessions` - 0 registros** 🟢

```
Status: VAZIA - nunca foi usada
Definição: app/models/database.py:703-721
Uso no código: 0 referências
Conflito: Duplica funcionalidade de LoginSession
```

**Conclusão:** Seguro remover (vazia + duplicada)

---

### **3. `business_hours` - 14 registros** 🔴

**DADOS REAIS ENCONTRADOS:**

```
business_id: 3
Horários completos da semana:
- Domingo (0): Fechado
- Segunda (1): 08:00-18:00 (almoço 12:00-13:00)
- Terça (2): 08:00-18:00 (almoço 12:00-13:00)
- Quarta (3): 08:00-18:00 (almoço 12:00-13:00)
- Quinta (4): 08:00-18:00 (almoço 12:00-13:00)
- Sexta (5): 08:00-18:00 (almoço 12:00-13:00)
- Sábado (6): 08:00-14:00 (sem almoço)
```

**Problema:**
- ⚠️ Tabela **TEM DADOS** mas **NUNCA É LIDA** no código
- ⚠️ Sistema usa `Business.business_hours` (JSON) ao invés desta tabela
- ⚠️ **DADOS PERDIDOS** - usuário criou horários que não são usados!

**Opções:**
1. 🔄 **Migrar** dados para `Business.business_hours` (JSON)
2. 🔧 **Implementar** leitura desta tabela no código
3. ❌ **Deletar** (perde dados do usuário)

---

### **4. `business_policies` - 3 registros** 🔴

**DADOS REAIS ENCONTRADOS:**

```
1. Política de Cancelamento (business_id: 1)
   - Cancelamento com 24h de antecedência
   - Sem reembolso
   
2. Política de Reagendamento (business_id: 1)
   - Até 2h antes do horário
   - Máximo 2 reagendamentos

3. Política de Falta (No-show) (business_id: 1)
   - Taxa de 50% por falta
   - Grace period: 15 minutos
```

**Problema:**
- ⚠️ Tabela **TEM DADOS** mas **NUNCA É LIDA** no código
- ⚠️ Políticas criadas mas não aplicadas
- ⚠️ **FUNCIONALIDADE IMPLEMENTADA MAS NÃO USADA**

**Opções:**
1. 🔧 **Implementar** leitura e aplicação das políticas
2. 📋 **Exportar** para documentação e deletar
3. ❌ **Deletar** (perde configurações)

---

### **5. `payment_methods` - 4 registros** 🔴

**DADOS REAIS ENCONTRADOS:**

```
business_id: 1
Métodos de pagamento cadastrados:

1. Dinheiro (ordem: 1)
   - Pagamento em espécie
   
2. PIX (ordem: 2)
   - Transferência instantânea
   
3. Cartão de Débito (ordem: 3)
   
4. Cartão de Crédito (ordem: 4)
```

**Problema:**
- ⚠️ Tabela **TEM DADOS** mas **NUNCA É LIDA** no código
- ⚠️ Métodos de pagamento configurados mas não exibidos
- ⚠️ **FUNCIONALIDADE IMPLEMENTADA MAS NÃO USADA**

**Opções:**
1. 🔧 **Implementar** exibição de métodos de pagamento
2. 📋 **Exportar** para documentação e deletar
3. ❌ **Deletar** (perde configurações)

---

### **6. `auth_users` - 4 registros** 🔴

**DADOS REAIS ENCONTRADOS:**

```
4 usuários cadastrados (com senhas hasheadas):

1. admin@exemplo.com (ID: 1, role: admin)
   - Nome: Administrador
   - company_id: 1
   - Último login: 2025-09-04 15:59:38
   - Status: ATIVO

2. debug_admin_f3f6f090@test.com (ID: 5, role: admin)
   - Usuário de debug
   - Criado: 2025-09-10
   - Nunca fez login
   
3. admin@sistema.local (ID: 6, role: admin)
   - Criado: 2025-09-02
   - Nunca fez login
   
4. admin_producao_seguro@sistema.local (ID: 7, role: admin)
   - Criado: 2025-09-11
   - Nunca fez login
```

**Problema CRÍTICO:**
- 🚨 **CONFLITA** com `AdminUser` (3 usuários ativos)
- 🚨 Sistema usa apenas `AdminUser`, estes usuários **NUNCA FAZEM LOGIN**
- 🚨 **DUPLICAÇÃO DE AUTENTICAÇÃO** - dois sistemas paralelos
- 🚨 Senhas armazenadas mas nunca validadas
- 🚨 Último login em 04/09 do usuário #1, mas sistema atual não usa esta tabela!

**Conclusão:**
- ⚠️ Tabela de um sistema de autenticação **ANTIGO/ABANDONADO**
- ⚠️ `AdminUser` é o sistema **ATIVO** (usado em produção)
- ⚠️ Estes 4 usuários **NÃO CONSEGUEM LOGAR** no sistema atual

---

## 🎯 ANÁLISE CONSOLIDADA

### **Tabelas Vazias (Seguras para Remover):**
- ✅ `login_attempts` - 0 registros, nunca usada
- ✅ `user_sessions` - 0 registros, duplica `LoginSession`

### **Tabelas com Dados (Decisão Necessária):**
- ⚠️ `business_hours` - 14 registros (horários da semana)
- ⚠️ `business_policies` - 3 registros (políticas de negócio)
- ⚠️ `payment_methods` - 4 registros (métodos de pagamento)
- 🚨 `auth_users` - 4 registros (usuários do sistema antigo)

---

## 💡 RECOMENDAÇÕES POR TABELA

### **1. login_attempts & user_sessions:**
**✅ AÇÃO: REMOVER**
- Vazias
- Nunca usadas
- Risco: ZERO

### **2. business_hours:**
**🔄 AÇÃO: MIGRAR DADOS**
```python
# Opção 1: Migrar para Business.business_hours (JSON)
# Converter 14 registros para formato JSON e salvar em Business

# Opção 2: Implementar leitura desta tabela
# Criar API para ler/escrever business_hours estruturado
```

### **3. business_policies:**
**📋 AÇÃO: EXPORTAR E DEPOIS DECIDIR**
```python
# Exportar para JSON/Markdown
# Decidir se implementar ou apenas documentar
```

### **4. payment_methods:**
**📋 AÇÃO: EXPORTAR E DEPOIS DECIDIR**
```python
# Exportar configuração
# Decidir se implementar ou apenas documentar
```

### **5. auth_users:**
**🚨 AÇÃO: ANALISAR CUIDADOSAMENTE**
```python
# PERIGO: Pode ter usuários legítimos do sistema antigo
# Verificar se algum usuário ainda precisa acessar
# Considerar migração para AdminUser
```

---

## 📝 PLANO DE AÇÃO PROPOSTO

### **Fase 1: Exportar Dados (BACKUP)**
```bash
# Exportar todas as tabelas para JSON
pg_dump -t business_hours -t business_policies \
        -t payment_methods -t auth_users \
        --data-only --column-inserts \
        $DATABASE_URL > orphan_tables_backup.sql
```

### **Fase 2: Criar Scripts de Migração**
```python
# Script para migrar business_hours -> Business.business_hours (JSON)
# Script para verificar auth_users vs AdminUser
```

### **Fase 3: Remover Tabelas Vazias**
```sql
DROP TABLE IF EXISTS login_attempts CASCADE;
DROP TABLE IF EXISTS user_sessions CASCADE;
```

### **Fase 4: Decidir sobre Tabelas com Dados**
- Migrar ou deletar após backup

---

## ❓ PERGUNTAS PARA O USUÁRIO

1. **business_hours (14 registros):**
   - Quer **migrar** para JSON? 
   - Quer **implementar** leitura desta tabela?
   - Pode **deletar**?

2. **business_policies (3 registros):**
   - Quer **implementar** sistema de políticas?
   - Apenas **documentar** e deletar?

3. **payment_methods (4 registros):**
   - Quer **implementar** exibição de métodos?
   - Apenas **documentar** e deletar?

4. **auth_users (4 usuários):**
   - Algum destes usuários ainda precisa acessar?
   - Pode **migrar** para AdminUser?
   - Pode **deletar** (são do sistema antigo)?

---

## 🚨 DECISÃO NECESSÁRIA

**Eu posso:**

1. ✅ **Remover tabelas vazias** agora (`login_attempts`, `user_sessions`)
2. 📦 **Fazer backup** de todas as tabelas com dados
3. 🔄 **Migrar** `business_hours` para JSON
4. 📋 **Exportar** policies e payment_methods
5. 🔍 **Analisar** auth_users vs AdminUser

**O que você quer fazer primeiro?**

---

**🎯 Total de dados em risco: 25 registros (14 + 3 + 4 + 4)**

