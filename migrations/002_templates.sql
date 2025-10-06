-- Migration: Criar tabela de templates
-- Data: 2025-10-05
-- Descrição: Sistema de templates para mensagens WhatsApp

-- Criar tabela templates
CREATE TABLE IF NOT EXISTS templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    language VARCHAR(10) DEFAULT 'pt-BR',
    content TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    variables TEXT[], -- Array de variáveis {name}, {date}, etc
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    approved_at TIMESTAMP WITH TIME ZONE,
    rejected_at TIMESTAMP WITH TIME ZONE,
    rejection_reason TEXT
);

-- Índices para melhor performance
CREATE INDEX IF NOT EXISTS idx_templates_category ON templates(category);
CREATE INDEX IF NOT EXISTS idx_templates_status ON templates(status);
CREATE INDEX IF NOT EXISTS idx_templates_created_at ON templates(created_at);

-- Trigger para atualizar updated_at automaticamente
CREATE OR REPLACE FUNCTION update_templates_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS trigger_update_templates_updated_at ON templates;
CREATE TRIGGER trigger_update_templates_updated_at 
    BEFORE UPDATE ON templates
    FOR EACH ROW 
    EXECUTE FUNCTION update_templates_updated_at();

-- Inserir templates de exemplo
INSERT INTO templates (name, category, language, content, status, variables, approved_at)
VALUES 
    ('Confirmação de Agendamento', 'agendamento', 'pt-BR', 
     'Olá {{1}}! Seu agendamento para {{2}} foi confirmado para {{3}} às {{4}}. Aguardamos você!', 
     'aprovado', ARRAY['{{1}}', '{{2}}', '{{3}}', '{{4}}'], NOW()),
     
    ('Lembrete de Consulta', 'lembrete', 'pt-BR',
     'Lembrete: Sua consulta está marcada para amanhã às {{1}}. Não esqueça!',
     'aprovado', ARRAY['{{1}}'], NOW()),
     
    ('Promoção Especial', 'marketing', 'pt-BR',
     '🎉 Oferta especial! {{1}} de desconto em todos os serviços até {{2}}. Agende já!',
     'pendente', ARRAY['{{1}}', '{{2}}'], NULL),
     
    ('Código de Verificação', 'autenticacao', 'pt-BR',
     'Seu código de verificação é: {{1}}. Válido por 5 minutos.',
     'rejeitado', ARRAY['{{1}}'], NULL),
     
    ('Cancelamento de Agendamento', 'transacional', 'pt-BR',
     'Seu agendamento de {{1}} foi cancelado. Entre em contato para reagendar.',
     'aprovado', ARRAY['{{1}}'], NOW())
ON CONFLICT DO NOTHING;

-- Atualizar rejection_reason para template rejeitado
UPDATE templates 
SET rejected_at = NOW(), 
    rejection_reason = 'Formato de código não está claro'
WHERE name = 'Código de Verificação';

-- Verificar instalação
SELECT 'Migration 002_templates concluída com sucesso!' as status;
SELECT COUNT(*) as total_templates FROM templates;

