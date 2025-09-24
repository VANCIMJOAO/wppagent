import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  try {
    console.log('📈 API: Série temporal solicitada');
    
    const searchParams = request.nextUrl.searchParams;
    const metric = searchParams.get('metric') || 'conversations';
    const period = searchParams.get('period') || 'day';
    const startDate = searchParams.get('start_date');
    const endDate = searchParams.get('end_date');
    
    // Mock data para série temporal
    const timeseriesData = {
      success: true,
      data: {
        metric: metric,
        metric_type: metric, // Adicionar metric_type para compatibilidade
        period: period,
        start_date: startDate,
        end_date: endDate,
        data: [
          { date: '2025-08-25', value: 12 },
          { date: '2025-08-26', value: 15 },
          { date: '2025-08-27', value: 18 },
          { date: '2025-08-28', value: 14 },
          { date: '2025-08-29', value: 20 },
          { date: '2025-08-30', value: 16 },
          { date: '2025-08-31', value: 22 },
          { date: '2025-09-01', value: 19 },
          { date: '2025-09-02', value: 25 },
          { date: '2025-09-03', value: 21 },
          { date: '2025-09-04', value: 17 },
          { date: '2025-09-05', value: 23 },
          { date: '2025-09-06', value: 20 },
          { date: '2025-09-07', value: 26 },
          { date: '2025-09-08', value: 24 },
          { date: '2025-09-09', value: 28 },
          { date: '2025-09-10', value: 25 },
          { date: '2025-09-11', value: 30 },
          { date: '2025-09-12', value: 27 },
          { date: '2025-09-13', value: 32 },
          { date: '2025-09-14', value: 29 },
          { date: '2025-09-15', value: 35 },
          { date: '2025-09-16', value: 31 },
          { date: '2025-09-17', value: 33 },
          { date: '2025-09-18', value: 30 },
          { date: '2025-09-19', value: 36 },
          { date: '2025-09-20', value: 34 },
          { date: '2025-09-21', value: 38 },
          { date: '2025-09-22', value: 35 },
          { date: '2025-09-23', value: 40 },
          { date: '2025-09-24', value: 37 }
        ]
      }
    };

    console.log(`✅ Série temporal para ${metric} retornada com sucesso`);
    return NextResponse.json(timeseriesData);

  } catch (error) {
    console.error('❌ Erro ao buscar série temporal:', error);
    return NextResponse.json(
      {
        success: false,
        error: 'Erro interno do servidor',
        details: error instanceof Error ? error.message : 'Erro desconhecido'
      },
      { status: 500 }
    );
  }
}
