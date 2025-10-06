# 🚀 Migrações do Dashboard - Guia de Aplicação

**Data:** 03/10/2025  
**Objetivo:** Transformar dashboard de mock para dados reais

---

## ⚡ Quick Start

### **Opção 1: Script SQL Direto** (Recomendado)

```bash
# Conectar ao PostgreSQL e executar
psql -U seu_usuario -d whatsapp_agent -f migrations/001_dashboard_fields.sql

# Ou via docker (se usando)
docker exec -i postgres_container psql -U postgres -d whatsapp_agent < migrations/001_dashboard_fields.sql
```

### **Opção 2: Alembic Migration**

```bash
cd /home/vancim/whats_agent
source .venv/bin/activate
alembic upgrade head
```

---

## 📋 O Que Será Criado

### **1. Campo Novo em `conversations`**
```sql
ALTER TABLE conversations 
ADD COLUMN first_response_at TIMESTAMP WITH TIME ZONE;
```

### **2. Tabela Nova `customer_feedback`**
```sql
CREATE TABLE customer_feedback (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER REFERENCES conversations(id),
    user_id INTEGER REFERENCES users(id),
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### **3. Índices de Performance (7 novos)**
- `idx_conversations_first_response`
- `idx_conversations_created_status`
- `idx_messages_created_at`
- `idx_appointments_created_at`
- `idx_feedback_created_at`
- `idx_feedback_rating`
- `idx_feedback_conversation`

---

## ✅ Verificação

Após aplicar, verifique se tudo foi criado:

```sql
-- Verificar campo novo
SELECT column_name 
FROM information_schema.columns
WHERE table_name = 'conversations' AND column_name = 'first_response_at';

-- Verificar tabela nova
SELECT COUNT(*) FROM customer_feedback;

-- Verificar índices
SELECT indexname 
FROM pg_indexes 
WHERE tablename IN ('conversations', 'customer_feedback', 'messages', 'appointments')
AND indexname LIKE 'idx_%'
ORDER BY indexname;
```

---

## 🎯 Próximos Passos

1. ✅ Aplicar migração
2. 🔄 Reiniciar servidor backend
3. 🧪 Testar endpoint: `curl http://localhost:8000/api/dashboard?days=30`
4. 🎨 Verificar frontend: `http://localhost:3000/dashboard`
5. 📊 Dados reais devem aparecer!

---

## 🔧 Troubleshooting

### **Erro: Column already exists**
```
Solução: Campo já foi criado anteriormente, pode ignorar
```

### **Erro: Table already exists**
```
Solução: Tabela já existe, pode ignorar
```

### **Erro: Permission denied**
```
Solução: Use usuário com permissões CREATE TABLE e ALTER TABLE
```

---

## 📞 Suporte

Se algo não funcionar:
1. Verifique os logs do PostgreSQL
2. Confirme que o banco está acessível
3. Verifique permissões do usuário
4. Consulte: `DASHBOARD_MOCK_DATA_ANALYSIS.md` para detalhes completos

---

**Boa sorte! 🚀**

