import { NextResponse } from 'next/server';
import { Pool } from 'pg';
import { debugLog } from '@/lib/debug';

// Configuração do banco PostgreSQL
const pool = new Pool({
  connectionString: process.env.DATABASE_URL || 'postgresql://postgres:UGARTPCwAADBBeBLctoRnQXLsoUvLJxz@caboose.proxy.rlwy.net:13910/railway',
  ssl: {
    rejectUnauthorized: false
  }
});

export async function GET() {
  let client;
  
  try {
    debugLog.info('📊 Buscando dados reais do dashboard do PostgreSQL...');
    
    client = await pool.connect();
    
    // Buscar métricas principais
    const metricsQuery = `
      SELECT 
        COUNT(DISTINCT u.id) as total_customers,
        COUNT(DISTINCT c.id) as total_conversations,
        COUNT(DISTINCT a.id) as total_appointments,
        COUNT(DISTINCT m.id) as total_messages,
        COUNT(DISTINCT CASE WHEN c.status = 'active' THEN c.id END) as active_conversations,
        COUNT(DISTINCT CASE WHEN a.status = 'confirmado' THEN a.id END) as confirmed_appointments
      FROM users u
      LEFT JOIN conversations c ON u.id = c.user_id
      LEFT JOIN appointments a ON u.id = a.user_id
      LEFT JOIN messages m ON u.id = m.user_id
    `;
    
    const metricsResult = await client.query(metricsQuery);
    const metrics = metricsResult.rows[0];
    
    // Buscar conversas recentes
    const recentConversationsQuery = `
      SELECT 
        c.id,
        u.nome as customer_name,
        u.telefone as customer_phone,
        c.status,
        c.last_message_at,
        c.created_at,
        COUNT(m.id) as message_count
      FROM conversations c
      JOIN users u ON c.user_id = u.id
      LEFT JOIN messages m ON c.id = m.conversation_id
      GROUP BY c.id, u.nome, u.telefone, c.status, c.last_message_at, c.created_at
      ORDER BY c.last_message_at DESC
      LIMIT 10
    `;
    
    const recentConversationsResult = await client.query(recentConversationsQuery);
    
    // Buscar agendamentos recentes
    const recentAppointmentsQuery = `
      SELECT 
        a.id,
        u.nome as customer_name,
        u.telefone as customer_phone,
        a.status,
        a.date_time,
        a.created_at
      FROM appointments a
      JOIN users u ON a.user_id = u.id
      ORDER BY a.date_time DESC
      LIMIT 10
    `;
    
    const recentAppointmentsResult = await client.query(recentAppointmentsQuery);
    
    // Calcular taxa de conversão (conversas que resultaram em agendamentos)
    const conversionRate = metrics.total_conversations > 0 
      ? ((metrics.confirmed_appointments / metrics.total_conversations) * 100).toFixed(1)
      : '0.0';
    
    // Calcular tempo médio de resposta (simulado por enquanto)
    const avgResponseTime = 2.5; // minutos
    
    // Calcular satisfação média (simulado por enquanto)
    const avgSatisfaction = 4.2; // de 5.0
    
    const dashboardData = {
      key_metrics: {
        total_customers: parseInt(metrics.total_customers) || 0,
        total_conversations: parseInt(metrics.total_conversations) || 0,
        total_appointments: parseInt(metrics.total_appointments) || 0,
        total_messages: parseInt(metrics.total_messages) || 0,
        active_conversations: parseInt(metrics.active_conversations) || 0,
        confirmed_appointments: parseInt(metrics.confirmed_appointments) || 0,
        overall_conversion_rate: parseFloat(conversionRate),
        avg_response_time_minutes: avgResponseTime,
        satisfaction_score: avgSatisfaction,
        total_revenue: 0, // Não implementado ainda
        roi_percentage: 0 // Não implementado ainda
      },
      recent_activity: [
        ...recentConversationsResult.rows.map(conv => ({
          id: conv.id,
          type: 'conversation',
          message: `Nova conversa com ${conv.customer_name || 'Cliente'}`,
          timestamp: conv.last_message_at,
          status: conv.status,
          customer_name: conv.customer_name,
          customer_phone: conv.customer_phone,
          message_count: conv.message_count
        })),
        ...recentAppointmentsResult.rows.map(apt => ({
          id: apt.id,
          type: 'appointment',
          message: `Agendamento confirmado com ${apt.customer_name || 'Cliente'}`,
          timestamp: apt.date_time,
          status: apt.status,
          customer_name: apt.customer_name,
          customer_phone: apt.customer_phone
        }))
      ].sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()).slice(0, 10),
      performance_trends: {
        daily_conversations: [12, 15, 8, 20, 18, 25, 22], // Simulado por enquanto
        daily_revenue: [1200, 1500, 800, 2000, 1800, 2500, 2200], // Simulado por enquanto
        conversion_rates: [12.5, 15.2, 8.1, 20.3, 18.7, 25.1, 22.4] // Simulado por enquanto
      }
    };
    
    debugLog.success('Dados reais do dashboard obtidos:', {
      customers: dashboardData.key_metrics.total_customers,
      conversations: dashboardData.key_metrics.total_conversations,
      appointments: dashboardData.key_metrics.total_appointments,
      messages: dashboardData.key_metrics.total_messages
    });
    
    return NextResponse.json(dashboardData);
    
  } catch (error) {
    debugLog.error('Erro ao buscar dados do dashboard:', error);
    return NextResponse.json(
      { error: 'Erro ao buscar dados do dashboard' },
      { status: 500 }
    );
  } finally {
    if (client) {
      client.release();
    }
  }
}
