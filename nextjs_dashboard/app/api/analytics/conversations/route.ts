/**
 * Analytics Conversations API - Dados específicos de conversas
 * Funil detalhado e análises de conversão
 */
import { NextRequest, NextResponse } from 'next/server';
import { format, subDays, parseISO } from 'date-fns';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    
    // Parâmetros de filtro
    const startDate = searchParams.get('start_date') || format(subDays(new Date(), 30), 'yyyy-MM-dd');
    const endDate = searchParams.get('end_date') || format(new Date(), 'yyyy-MM-dd');
    const status = searchParams.get('status')?.split(',') || [];
    const tags = searchParams.get('tags')?.split(',') || [];

    // Dados detalhados de conversas
    const conversationsData = {
      conversationsOverTime: generateDetailedTimeSeriesData(startDate, endDate),
      funnelData: [
        { stage: 'Contato Inicial', count: 2850, conversionRate: 100, previousStage: 2850 },
        { stage: 'Primeira Resposta', count: 2420, conversionRate: 84.9, previousStage: 2850 },
        { stage: 'Conversa Ativa', count: 1890, conversionRate: 78.1, previousStage: 2420 },
        { stage: 'Interesse Demonstrado', count: 980, conversionRate: 51.9, previousStage: 1890 },
        { stage: 'Agendamento Solicitado', count: 420, conversionRate: 42.9, previousStage: 980 },
        { stage: 'Agendamento Confirmado', count: 285, conversionRate: 67.9, previousStage: 420 },
        { stage: 'Atendimento Realizado', count: 240, conversionRate: 84.2, previousStage: 285 },
      ],
      satisfactionBreakdown: [
        { rating: 5, count: 1450, percentage: 60.4, trend: 8.2 },
        { rating: 4, count: 620, percentage: 25.8, trend: 3.1 },
        { rating: 3, count: 220, percentage: 9.2, trend: -2.8 },
        { rating: 2, count: 75, percentage: 3.1, trend: -4.2 },
        { rating: 1, count: 35, percentage: 1.5, trend: -4.3 },
      ],
      conversationTopics: [
        { topic: 'Agendamento', count: 850, percentage: 29.8 },
        { topic: 'Informações', count: 720, percentage: 25.3 },
        { topic: 'Suporte Técnico', count: 485, percentage: 17.0 },
        { topic: 'Cancelamento', count: 320, percentage: 11.2 },
        { topic: 'Reagendamento', count: 285, percentage: 10.0 },
        { topic: 'Outros', count: 190, percentage: 6.7 },
      ],
      responseTimeDistribution: [
        { range: '< 30s', count: 1200, percentage: 42.1, avgTime: 18 },
        { range: '30s - 1min', count: 850, percentage: 29.8, avgTime: 45 },
        { range: '1min - 2min', count: 485, percentage: 17.0, avgTime: 87 },
        { range: '2min - 5min', count: 220, percentage: 7.7, avgTime: 180 },
        { range: '> 5min', count: 95, percentage: 3.3, avgTime: 420 },
      ],
      conversationOutcomes: [
        { outcome: 'Agendamento Realizado', count: 285, percentage: 10.0, satisfaction: 4.8 },
        { outcome: 'Informação Fornecida', count: 1250, percentage: 43.9, satisfaction: 4.5 },
        { outcome: 'Problema Resolvido', count: 720, percentage: 25.3, satisfaction: 4.7 },
        { outcome: 'Encaminhamento', count: 380, percentage: 13.3, satisfaction: 4.2 },
        { outcome: 'Não Resolvido', count: 215, percentage: 7.5, satisfaction: 3.1 },
      ],
      totalConversations: 2850,
      activeConversations: 145,
      pendingConversations: 28,
      resolvedConversations: 2677,
      avgConversationDuration: 8.5, // minutos
      peakHours: [
        { hour: '09:00', conversations: 180 },
        { hour: '10:00', conversations: 220 },
        { hour: '11:00', conversations: 195 },
        { hour: '14:00', conversations: 210 },
        { hour: '15:00', conversations: 185 },
        { hour: '16:00', conversations: 165 },
      ],
    };

    return NextResponse.json({
      success: true,
      data: conversationsData,
      message: 'Dados de conversas carregados com sucesso',
    });

  } catch (error) {
    console.error('Erro ao carregar dados de conversas:', error);
    return NextResponse.json(
      { 
        success: false, 
        error: 'Erro interno do servidor',
        message: 'Falha ao carregar dados de conversas'
      },
      { status: 500 }
    );
  }
}

// Função para gerar dados detalhados de série temporal
function generateDetailedTimeSeriesData(startDate: string, endDate: string) {
  const start = parseISO(startDate);
  const end = parseISO(endDate);
  const data = [];
  
  let current = start;
  while (current <= end) {
    const dayOfWeek = current.getDay();
    const isWeekend = dayOfWeek === 0 || dayOfWeek === 6;
    
    // Variação mais realista por dia da semana
    const multiplier = isWeekend ? 0.6 : 1.0;
    
    const conversations = Math.floor((90 + (Math.random() * 60)) * multiplier);
    const messages = Math.floor((conversations * 3.5) + (Math.random() * 50) - 25);
    const responses = Math.floor(conversations * (0.82 + (Math.random() * 0.15)));
    
    data.push({
      date: format(current, 'yyyy-MM-dd'),
      conversations,
      messages,
      responses,
      responseRate: Math.round((responses / conversations) * 100),
      avgResponseTime: Math.floor(25 + (Math.random() * 40)), // segundos
      satisfaction: Number((4.2 + (Math.random() * 0.8)).toFixed(1)),
    });
    
    current = new Date(current.getTime() + 24 * 60 * 60 * 1000);
  }
  
  return data;
}
