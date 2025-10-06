import { NextRequest, NextResponse } from 'next/server';
import { debugLog } from '@/lib/debug';

export async function GET(request: NextRequest) {
  try {
    debugLog.info('🔄 API: Funnel de conversão solicitado');
    
    // Mock data para o funil de conversão
    const funnelData = {
      success: true,
      data: {
        stages: [
          { stage: 'Leads', count: 150, percentage: 100 },
          { stage: 'Interessados', count: 75, percentage: 50 },
          { stage: 'Negociação', count: 30, percentage: 20 },
          { stage: 'Clientes', count: 15, percentage: 10 }
        ],
        lead_to_interested_rate: 50.0,
        interested_to_negotiation_rate: 40.0,
        negotiation_to_client_rate: 50.0,
        overall_conversion_rate: 10.0
      }
    };

    debugLog.success('Funnel de conversão retornado com sucesso');
    return NextResponse.json(funnelData);

  } catch (error) {
    debugLog.error('Erro ao buscar funnel de conversão:', error);
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
