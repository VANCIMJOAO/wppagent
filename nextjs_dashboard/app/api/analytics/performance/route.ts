/**
 * Analytics Performance API - Métricas de performance e KPIs
 * Dados de desempenho de agentes e sistema
 */
import { NextRequest, NextResponse } from 'next/server';
import { format, subDays } from 'date-fns';

// Force dynamic rendering for this route since it uses searchParams
export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest) {
  try {
    // Usar nextUrl.searchParams ao invés de new URL(request.url) para compatibilidade estática
    const searchParams = request.nextUrl.searchParams;
    
    // Parâmetros de filtro
    const startDate = searchParams.get('start_date') || format(subDays(new Date(), 30), 'yyyy-MM-dd');
    const endDate = searchParams.get('end_date') || format(new Date(), 'yyyy-MM-dd');
    const agents = searchParams.get('agents')?.split(',') || [];

    // Dados de performance
    const performanceData = {
      agentPerformance: [
        {
          agentId: 'agent_001',
          agentName: 'Maria Silva',
          conversations: 245,
          avgResponseTime: 28,
          satisfaction: 4.8,
          resolutionRate: 0.94,
          hoursWorked: 168,
          conversationsPerHour: 1.46,
          tags: ['especialista', 'senior'],
          lastActive: '2025-09-08T18:30:00Z',
        },
        {
          agentId: 'agent_002',
          agentName: 'João Santos',
          conversations: 198,
          avgResponseTime: 32,
          satisfaction: 4.6,
          resolutionRate: 0.91,
          hoursWorked: 160,
          conversationsPerHour: 1.24,
          tags: ['pleno'],
          lastActive: '2025-09-08T17:45:00Z',
        },
        {
          agentId: 'agent_003',
          agentName: 'Ana Costa',
          conversations: 220,
          avgResponseTime: 25,
          satisfaction: 4.9,
          resolutionRate: 0.96,
          hoursWorked: 172,
          conversationsPerHour: 1.28,
          tags: ['especialista', 'team-lead'],
          lastActive: '2025-09-08T18:20:00Z',
        },
        {
          agentId: 'agent_004',
          agentName: 'Pedro Oliveira',
          conversations: 165,
          avgResponseTime: 38,
          satisfaction: 4.4,
          resolutionRate: 0.87,
          hoursWorked: 152,
          conversationsPerHour: 1.09,
          tags: ['junior'],
          lastActive: '2025-09-08T16:30:00Z',
        },
        {
          agentId: 'agent_005',
          agentName: 'Carla Mendes',
          conversations: 185,
          avgResponseTime: 30,
          satisfaction: 4.7,
          resolutionRate: 0.92,
          hoursWorked: 164,
          conversationsPerHour: 1.13,
          tags: ['pleno'],
          lastActive: '2025-09-08T18:10:00Z',
        },
      ],
      systemPerformance: {
        uptime: 99.8,
        avgSystemResponseTime: 145, // ms
        peakConcurrentUsers: 285,
        totalApiCalls: 45280,
        errorRate: 0.12,
        successfulDeliveries: 99.3,
        queueLength: 12,
        processingCapacity: 95.2,
      },
      performanceTrends: [
        { 
          date: '2025-09-01', 
          responseTime: 32, 
          satisfaction: 4.5, 
          resolutionRate: 89, 
          conversations: 180 
        },
        { 
          date: '2025-09-02', 
          responseTime: 30, 
          satisfaction: 4.6, 
          resolutionRate: 91, 
          conversations: 195 
        },
        { 
          date: '2025-09-03', 
          responseTime: 28, 
          satisfaction: 4.6, 
          resolutionRate: 92, 
          conversations: 210 
        },
        { 
          date: '2025-09-04', 
          responseTime: 31, 
          satisfaction: 4.7, 
          resolutionRate: 93, 
          conversations: 185 
        },
        { 
          date: '2025-09-05', 
          responseTime: 29, 
          satisfaction: 4.8, 
          resolutionRate: 94, 
          conversations: 220 
        },
        { 
          date: '2025-09-06', 
          responseTime: 27, 
          satisfaction: 4.7, 
          resolutionRate: 93, 
          conversations: 175 
        },
        { 
          date: '2025-09-07', 
          responseTime: 26, 
          satisfaction: 4.8, 
          resolutionRate: 95, 
          conversations: 165 
        },
        { 
          date: '2025-09-08', 
          responseTime: 28, 
          satisfaction: 4.9, 
          resolutionRate: 96, 
          conversations: 240 
        },
      ],
      kpiMetrics: {
        firstResponseTime: {
          current: 28.5,
          target: 30,
          trend: -8.2,
          status: 'excellent'
        },
        resolutionTime: {
          current: 285, // segundos
          target: 300,
          trend: -12.5,
          status: 'good'
        },
        customerSatisfaction: {
          current: 4.7,
          target: 4.5,
          trend: 15.8,
          status: 'excellent'
        },
        firstContactResolution: {
          current: 87.5,
          target: 85,
          trend: 8.9,
          status: 'good'
        },
      },
      alerts: [
        {
          id: 'alert_001',
          type: 'warning',
          message: 'Pedro Oliveira com taxa de resolução abaixo da meta (87% vs 90%)',
          timestamp: '2025-09-08T17:30:00Z',
          resolved: false,
        },
        {
          id: 'alert_002',
          type: 'success',
          message: 'Sistema atingiu 99.8% de uptime neste mês',
          timestamp: '2025-09-08T16:00:00Z',
          resolved: true,
        },
        {
          id: 'alert_003',
          type: 'info',
          message: 'Pico de conversas detectado no período da tarde (14-16h)',
          timestamp: '2025-09-08T15:30:00Z',
          resolved: true,
        },
      ],
    };

    return NextResponse.json({
      success: true,
      data: performanceData,
      message: 'Dados de performance carregados com sucesso',
    });

  } catch (error) {
    console.error('Erro ao carregar dados de performance:', error);
    return NextResponse.json(
      { 
        success: false, 
        error: 'Erro interno do servidor',
        message: 'Falha ao carregar dados de performance'
      },
      { status: 500 }
    );
  }
}
