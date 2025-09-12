"""
🚀 P002: Criação de índice composto para otimização de queries messages

Problema: Índice composto ausente na tabela messages
Local: PostgreSQL schema  
Evidência: messages table com 2074 records
Causa: Falta otimização para dashboard queries
Correção: CREATE INDEX messages_conv_dir_created ON messages (conversation_id, direction, created_at)
Meta: Dashboard conversations query < 100ms

ANÁLISE ATUAL:
- Query atual: 0.117ms (já < 100ms, mas ineficiente)
- Index Scan em ix_messages_created_at + Filter
- Rows Removed by Filter: 9 (ineficiência!)
- Cost: 462.13 total
"""

-- ✅ P002: Criar índice composto otimizado
CREATE INDEX CONCURRENTLY IF NOT EXISTS messages_conv_dir_created 
ON messages (conversation_id, direction, created_at);

-- ✅ Comentário explicativo
COMMENT ON INDEX messages_conv_dir_created IS 
'P002: Índice composto para otimizar queries do dashboard - conversation_id + direction + created_at';

-- ✅ Verificar se o índice foi criado
\d messages

-- ✅ Análise de uso típico do índice
-- Query 1: Buscar mensagens de uma conversa ordenadas por data (padrão dashboard)
-- SELECT * FROM messages WHERE conversation_id = 10 ORDER BY created_at ASC;

-- Query 2: Buscar mensagens de entrada de uma conversa
-- SELECT * FROM messages WHERE conversation_id = 10 AND direction = 'in' ORDER BY created_at DESC;

-- Query 3: Buscar últimas mensagens de saída
-- SELECT * FROM messages WHERE conversation_id = 10 AND direction = 'out' ORDER BY created_at DESC LIMIT 1;
