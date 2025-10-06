-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- MIGRAÇÃO: Campos para Dashboard
-- Data: 03/10/2025
-- Descrição: Adiciona campos e tabelas necessários para métricas do dashboard
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- 1. ADICIONAR CAMPO first_response_at em conversations
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

-- Adicionar campo (se não existir)
ALTER TABLE conversations 
ADD COLUMN IF NOT EXISTS first_response_at TIMESTAMP WITH TIME ZONE;

-- Criar índice para performance
CREATE INDEX IF NOT EXISTS idx_conversations_first_response 
ON conversations(first_response_at);

-- Atualizar registros existentes com primeira resposta
-- (preencher com a data da primeira mensagem 'out')
UPDATE conversations c
SET first_response_at = (
    SELECT MIN(m.created_at)
    FROM messages m
    WHERE m.conversation_id = c.id
      AND m.direction = 'out'
)
WHERE first_response_at IS NULL
  AND EXISTS (
    SELECT 1 FROM messages m 
    WHERE m.conversation_id = c.id AND m.direction = 'out'
  );

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- 2. CRIAR TABELA customer_feedback (se não existir)
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CREATE TABLE IF NOT EXISTS customer_feedback (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER REFERENCES conversations(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    feedback_type VARCHAR(50),  -- 'nps', 'csat', 'ces', etc
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Índices para customer_feedback
CREATE INDEX IF NOT EXISTS idx_feedback_created_at ON customer_feedback(created_at);
CREATE INDEX IF NOT EXISTS idx_feedback_rating ON customer_feedback(rating);
CREATE INDEX IF NOT EXISTS idx_feedback_conversation ON customer_feedback(conversation_id);
CREATE INDEX IF NOT EXISTS idx_feedback_user ON customer_feedback(user_id);

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- 3. ÍNDICES ADICIONAIS PARA PERFORMANCE DO DASHBOARD
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

-- Índice composto para queries de conversão por período
CREATE INDEX IF NOT EXISTS idx_conversations_created_status 
ON conversations(created_at, status);

-- Índice para queries de mensagens por período
CREATE INDEX IF NOT EXISTS idx_messages_created_at 
ON messages(created_at);

-- Índice para queries de agendamentos por período
CREATE INDEX IF NOT EXISTS idx_appointments_created_at 
ON appointments(created_at);

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- 4. DADOS DE EXEMPLO para customer_feedback (OPCIONAL)
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

-- Inserir alguns feedbacks de exemplo
INSERT INTO customer_feedback (conversation_id, user_id, rating, comment, feedback_type, created_at)
SELECT 
    c.id,
    c.user_id,
    (FLOOR(RANDOM() * 3) + 3)::INTEGER,  -- Rating entre 3 e 5
    CASE 
        WHEN RANDOM() < 0.5 THEN 'Ótimo atendimento!'
        ELSE 'Muito bom, obrigado!'
    END,
    'csat',
    c.created_at + INTERVAL '1 hour'
FROM conversations c
WHERE c.status IN ('closed', 'converted')
  AND c.created_at >= NOW() - INTERVAL '30 days'
  AND NOT EXISTS (
    SELECT 1 FROM customer_feedback cf WHERE cf.conversation_id = c.id
  )
LIMIT 50
ON CONFLICT DO NOTHING;

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- 5. TRIGGER para atualizar updated_at automaticamente
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CREATE OR REPLACE FUNCTION update_customer_feedback_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_customer_feedback_updated_at
BEFORE UPDATE ON customer_feedback
FOR EACH ROW
EXECUTE FUNCTION update_customer_feedback_updated_at();

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- VERIFICAÇÃO: Confirmar que tudo foi criado
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

-- Verificar coluna first_response_at
SELECT column_name, data_type 
FROM information_schema.columns
WHERE table_name = 'conversations' AND column_name = 'first_response_at';

-- Verificar tabela customer_feedback
SELECT table_name 
FROM information_schema.tables 
WHERE table_name = 'customer_feedback';

-- Verificar índices criados
SELECT indexname 
FROM pg_indexes 
WHERE tablename IN ('conversations', 'customer_feedback', 'messages', 'appointments')
ORDER BY indexname;

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- FIM DA MIGRAÇÃO
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

