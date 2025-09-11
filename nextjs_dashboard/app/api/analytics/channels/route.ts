/**
 * Analytics Channels API - Performance por canal de comunicação
 * Análise comparativa entre WhatsApp Business, Web, API
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
    const channels = searchParams.get('channels')?.split(',') || [];

    // Dados por canal
    const channelsData = {
      channelPerformance: [
        {
          channel: 'WhatsApp Business',
          conversations: 1680,
          messages: 6720,
          avgResponseTime: 32,
          satisfaction: 4.7,
          activeUsers: 285,
          conversionRate: 18.5,
          revenue: 45280,
          trends: {
            conversations: 12.8,
            satisfaction: 8.5,
            responseTime: -6.2,
          },
          demographics: {
            age: { '18-25': 15, '26-35': 35, '36-45': 28, '46-55': 18, '55+': 4 },
            gender: { 'male': 48, 'female': 52 },
            location: { 'SP': 42, 'RJ': 28, 'MG': 15, 'RS': 10, 'outros': 5 }
          },
        },
        {
          channel: 'WhatsApp Web',
          conversations: 980,
          messages: 3920,
          avgResponseTime: 28,
          satisfaction: 4.5,
          activeUsers: 165,
          conversionRate: 22.1,
          revenue: 28640,
          trends: {
            conversations: 8.9,
            satisfaction: 5.2,
            responseTime: -12.1,
          },
          demographics: {
            age: { '18-25': 28, '26-35': 42, '36-45': 20, '46-55': 8, '55+': 2 },
            gender: { 'male': 55, 'female': 45 },
            location: { 'SP': 38, 'RJ': 32, 'MG': 18, 'RS': 8, 'outros': 4 }
          },
        },
        {
          channel: 'API Integration',
          conversations: 520,
          messages: 2080,
          avgResponseTime: 18,
          satisfaction: 4.8,
          activeUsers: 95,
          conversionRate: 31.2,
          revenue: 18720,
          trends: {
            conversations: 25.4,
            satisfaction: 12.8,
            responseTime: -15.6,
          },
          demographics: {
            age: { '18-25': 22, '26-35': 38, '36-45': 25, '46-55': 12, '55+': 3 },
            gender: { 'male': 62, 'female': 38 },
            location: { 'SP': 45, 'RJ': 25, 'MG': 12, 'RS': 12, 'outros': 6 }
          },
        },
        {
          channel: 'WhatsApp Bot',
          conversations: 1250,
          messages: 2500,
          avgResponseTime: 5,
          satisfaction: 4.2,
          activeUsers: 420,
          conversionRate: 8.5,
          revenue: 12480,
          trends: {
            conversations: 18.7,
            satisfaction: -2.1,
            responseTime: 0,
          },
          demographics: {
            age: { '18-25': 35, '26-35': 32, '36-45': 20, '46-55': 10, '55+': 3 },
            gender: { 'male': 50, 'female': 50 },
            location: { 'SP': 40, 'RJ': 30, 'MG': 15, 'RS': 10, 'outros': 5 }
          },
        },
      ],
      channelComparison: {
        bestPerforming: 'API Integration',
        highestVolume: 'WhatsApp Business',
        fastestResponse: 'WhatsApp Bot',
        highestSatisfaction: 'API Integration',
        bestConversion: 'API Integration',
      },
      hourlyDistribution: [
        { hour: '00:00', whatsapp: 12, web: 8, api: 3, bot: 45 },
        { hour: '01:00', whatsapp: 8, web: 5, api: 2, bot: 38 },
        { hour: '02:00', whatsapp: 5, web: 3, api: 1, bot: 28 },
        { hour: '03:00', whatsapp: 3, web: 2, api: 1, bot: 22 },
        { hour: '04:00', whatsapp: 4, web: 3, api: 1, bot: 25 },
        { hour: '05:00', whatsapp: 8, web: 5, api: 2, bot: 35 },
        { hour: '06:00', whatsapp: 25, web: 15, api: 8, bot: 48 },
        { hour: '07:00', whatsapp: 45, web: 28, api: 12, bot: 65 },
        { hour: '08:00', whatsapp: 68, web: 42, api: 18, bot: 85 },
        { hour: '09:00', whatsapp: 85, web: 52, api: 25, bot: 95 },
        { hour: '10:00', whatsapp: 92, web: 58, api: 28, bot: 88 },
        { hour: '11:00', whatsapp: 88, web: 55, api: 26, bot: 82 },
        { hour: '12:00', whatsapp: 75, web: 48, api: 22, bot: 75 },
        { hour: '13:00', whatsapp: 65, web: 40, api: 18, bot: 68 },
        { hour: '14:00', whatsapp: 95, web: 62, api: 32, bot: 92 },
        { hour: '15:00', whatsapp: 98, web: 65, api: 35, bot: 95 },
        { hour: '16:00', whatsapp: 85, web: 55, api: 28, bot: 85 },
        { hour: '17:00', whatsapp: 75, web: 48, api: 25, bot: 78 },
        { hour: '18:00', whatsapp: 68, web: 42, api: 22, bot: 72 },
        { hour: '19:00', whatsapp: 58, web: 35, api: 18, bot: 65 },
        { hour: '20:00', whatsapp: 48, web: 30, api: 15, bot: 58 },
        { hour: '21:00', whatsapp: 38, web: 25, api: 12, bot: 52 },
        { hour: '22:00', whatsapp: 28, web: 18, api: 8, bot: 45 },
        { hour: '23:00', whatsapp: 18, web: 12, api: 5, bot: 38 },
      ],
      deviceBreakdown: {
        mobile: { percentage: 78.5, conversions: 15.2 },
        desktop: { percentage: 18.2, conversions: 28.9 },
        tablet: { percentage: 3.3, conversions: 12.8 },
      },
    };

    return NextResponse.json({
      success: true,
      data: channelsData,
      message: 'Dados de canais carregados com sucesso',
    });

  } catch (error) {
    console.error('Erro ao carregar dados de canais:', error);
    return NextResponse.json(
      { 
        success: false, 
        error: 'Erro interno do servidor',
        message: 'Falha ao carregar dados de canais'
      },
      { status: 500 }
    );
  }
}
