/**
 * Analytics Overview API - Dados gerais do sistema
 * Integração com backend para métricas principais
 */
import { NextRequest, NextResponse } from 'next/server';
import { format, subDays, parseISO } from 'date-fns';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    
    // Parâmetros de filtro
    const startDate = searchParams.get('start_date') || format(subDays(new Date(), 30), 'yyyy-MM-dd');
    const endDate = searchParams.get('end_date') || format(new Date(), 'yyyy-MM-dd');
    const channels = searchParams.get('channels')?.split(',') || [];
    const agents = searchParams.get('agents')?.split(',') || [];

    // Simular dados reais do analytics (em produção, viria do backend)
    const analyticsData = {
      conversationsOverTime: generateTimeSeriesData(startDate, endDate),
      funnelData: [
        { stage: 'Visitantes', count: 1250, conversionRate: 100, previousStage: 1250 },
        { stage: 'Iniciaram Conversa', count: 420, conversionRate: 33.6, previousStage: 1250 },
        { stage: 'Responderam', count: 285, conversionRate: 67.9, previousStage: 420 },
        { stage: 'Agendaram', count: 125, conversionRate: 43.9, previousStage: 285 },
        { stage: 'Confirmaram', count: 95, conversionRate: 76, previousStage: 125 },
      ],
      channelPerformance: [
        { 
          channel: 'WhatsApp Business', 
          conversations: 1250, 
          messages: 4800, 
          avgResponseTime: 45, 
          satisfaction: 4.6 
        },
        { 
          channel: 'WhatsApp Web', 
          conversations: 850, 
          messages: 3200, 
          avgResponseTime: 38, 
          satisfaction: 4.4 
        },
        { 
          channel: 'API Integration', 
          conversations: 450, 
          messages: 1800, 
          avgResponseTime: 25, 
          satisfaction: 4.8 
        },
      ],
      agentPerformance: [
        {
          agentId: 'agent_001',
          agentName: 'Maria Silva',
          conversations: 180,
          avgResponseTime: 32,
          satisfaction: 4.8,
          resolutionRate: 0.92
        },
        {
          agentId: 'agent_002', 
          agentName: 'João Santos',
          conversations: 145,
          avgResponseTime: 28,
          satisfaction: 4.6,
          resolutionRate: 0.89
        },
        {
          agentId: 'agent_003',
          agentName: 'Ana Costa',
          conversations: 165,
          avgResponseTime: 35,
          satisfaction: 4.7,
          resolutionRate: 0.94
        },
        {
          agentId: 'agent_004',
          agentName: 'Pedro Oliveira',
          conversations: 120,
          avgResponseTime: 41,
          satisfaction: 4.5,
          resolutionRate: 0.87
        },
      ],
      satisfactionBreakdown: [
        { rating: 5, count: 1200, percentage: 52.4, trend: 5.2 },
        { rating: 4, count: 680, percentage: 29.7, trend: 2.1 },
        { rating: 3, count: 280, percentage: 12.2, trend: -1.8 },
        { rating: 2, count: 90, percentage: 3.9, trend: -2.1 },
        { rating: 1, count: 40, percentage: 1.8, trend: -3.4 },
      ],
      totalConversations: 2850,
      totalMessages: 11500,
      avgResponseTime: 34,
      overallSatisfaction: 4.6,
      trends: {
        conversations: 15.2,
        responseTime: -8.4,
        satisfaction: 12.8,
      },
    };

    return NextResponse.json({
      success: true,
      data: analyticsData,
      message: 'Analytics overview carregado com sucesso',
    });

  } catch (error) {
    console.error('Erro ao carregar analytics overview:', error);
    return NextResponse.json(
      { 
        success: false, 
        error: 'Erro interno do servidor',
        message: 'Falha ao carregar dados analytics'
      },
      { status: 500 }
    );
  }
}

// Função auxiliar para gerar série temporal
function generateTimeSeriesData(startDate: string, endDate: string) {
  const start = parseISO(startDate);
  const end = parseISO(endDate);
  const data = [];
  
  let current = start;
  while (current <= end) {
    const dayOfWeek = current.getDay();
    const isWeekend = dayOfWeek === 0 || dayOfWeek === 6;
    
    // Simular variação realista baseada no dia da semana
    const baseConversations = isWeekend ? 80 : 120;
    const baseMessages = isWeekend ? 300 : 450;
    
    const conversations = Math.floor(baseConversations + (Math.random() * 40) - 20);
    const messages = Math.floor(baseMessages + (Math.random() * 150) - 75);
    const responses = Math.floor(conversations * 0.85 + (Math.random() * 10) - 5);
    
    data.push({
      date: format(current, 'yyyy-MM-dd'),
      conversations,
      messages,
      responses,
      responseRate: Math.round((responses / conversations) * 100),
    });
    
    // Avançar um dia
    current = new Date(current.getTime() + 24 * 60 * 60 * 1000);
  }
  
  return data;
}
