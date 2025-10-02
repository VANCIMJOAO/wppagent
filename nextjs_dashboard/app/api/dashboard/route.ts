import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  try {
    console.log('📊 API Dashboard: Iniciando carregamento de dados...');
    
    // Buscar dados do backend
    const backendUrl = process.env.RAILWAY_API_URL || 'http://localhost:8000';
    const response = await fetch(`${backendUrl}/api/dashboard`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Cookie': request.headers.get('cookie') || '',
      },
    });

    if (!response.ok) {
      console.error('❌ Erro na resposta do backend:', response.status, response.statusText);
      throw new Error(`Backend error: ${response.status}`);
    }

    const data = await response.json();
    console.log('✅ API Dashboard: Dados recebidos do backend:', data);

    // Retornar dados padronizados
    return NextResponse.json({
      success: true,
      data: data,
      message: 'Dashboard data loaded successfully'
    }, {
      status: 200,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
      },
    });

  } catch (error) {
    console.error('❌ Erro na API Dashboard:', error);
    
    // Retornar dados mock em caso de erro
    const mockData = {
      key_metrics: {
        total_customers: 150,
        total_messages: 1250,
        total_conversations: 89,
        total_appointments: 45,
        overall_conversion_rate: 12.5,
        avg_response_time_minutes: 2.3,
        satisfaction_score: 4.2
      },
      trends: {
        conversations: 15.2,
        responseTime: -8.5,
        satisfaction: 5.1
      },
      funnel: {
        stages: [
          { stage: 'Visitors', count: 1000, conversionRate: 100, previousStage: 0 },
          { stage: 'Interested', count: 250, conversionRate: 25, previousStage: 1000 },
          { stage: 'Engaged', count: 89, conversionRate: 35.6, previousStage: 250 },
          { stage: 'Converted', count: 45, conversionRate: 50.6, previousStage: 89 }
        ],
        overall_conversion: 4.5
      },
      channel_performance: [
        { channel: 'WhatsApp', conversations: 89, messages: 1250, avgResponseTime: 2.3, satisfaction: 4.2 },
        { channel: 'SMS', conversations: 12, messages: 45, avgResponseTime: 5.1, satisfaction: 3.8 }
      ],
      satisfaction_breakdown: [
        { rating: 5, count: 35, percentage: 77.8, trend: 12.5 },
        { rating: 4, count: 8, percentage: 17.8, trend: -5.2 },
        { rating: 3, count: 2, percentage: 4.4, trend: -2.1 }
      ],
      time_series: []
    };

    return NextResponse.json({
      success: true,
      data: mockData,
      message: 'Using mock data due to backend error'
    }, {
      status: 200,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
      },
    });
  }
}

export async function OPTIONS(request: NextRequest) {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    },
  });
}
