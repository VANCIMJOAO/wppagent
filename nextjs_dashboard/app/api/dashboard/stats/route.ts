import { NextRequest, NextResponse } from 'next/server';
import { executeQuery } from '@/lib/database';

export async function GET(request: NextRequest) {
  try {
    console.log('📊 API: Buscando estatísticas do dashboard...');

    // Buscar estatísticas em paralelo para melhor performance
    const [
      usersStats,
      conversationsStats,
      messagesStats,
      appointmentsStats,
      recentActivity
    ] = await Promise.all([
      // Estatísticas de usuários
      executeQuery(`
        SELECT 
          COUNT(*) as total_users,
          COUNT(CASE WHEN created_at >= NOW() - INTERVAL '7 days' THEN 1 END) as new_users_week,
          COUNT(CASE WHEN created_at >= NOW() - INTERVAL '30 days' THEN 1 END) as new_users_month,
          COUNT(CASE WHEN email IS NOT NULL AND email != '' THEN 1 END) as users_with_email,
          COUNT(CASE WHEN telefone IS NOT NULL AND telefone != '' THEN 1 END) as users_with_phone
        FROM users
      `),
      
      // Estatísticas de conversas
      executeQuery(`
        SELECT 
          COUNT(*) as total_conversations,
          COUNT(CASE WHEN created_at >= NOW() - INTERVAL '7 days' THEN 1 END) as new_conversations_week,
          COUNT(CASE WHEN last_message_at >= NOW() - INTERVAL '24 hours' THEN 1 END) as active_conversations_24h,
          COUNT(CASE WHEN status = 'active' THEN 1 END) as active_conversations,
          COUNT(CASE WHEN status = 'closed' THEN 1 END) as closed_conversations
        FROM conversations
      `),
      
      // Estatísticas de mensagens
      executeQuery(`
        SELECT 
          COUNT(*) as total_messages,
          COUNT(CASE WHEN created_at >= NOW() - INTERVAL '24 hours' THEN 1 END) as messages_24h,
          COUNT(CASE WHEN created_at >= NOW() - INTERVAL '7 days' THEN 1 END) as messages_week,
          COUNT(CASE WHEN direction = 'inbound' THEN 1 END) as inbound_messages,
          COUNT(CASE WHEN direction = 'outbound' THEN 1 END) as outbound_messages
        FROM messages
      `),
      
      // Estatísticas de agendamentos
      executeQuery(`
        SELECT 
          COUNT(*) as total_appointments,
          COUNT(CASE WHEN created_at >= NOW() - INTERVAL '7 days' THEN 1 END) as new_appointments_week,
          COUNT(CASE WHEN status = 'confirmed' THEN 1 END) as confirmed_appointments,
          COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_appointments,
          COUNT(CASE WHEN status = 'cancelled' THEN 1 END) as cancelled_appointments,
          COUNT(CASE WHEN date_time >= NOW() AND date_time <= NOW() + INTERVAL '7 days' THEN 1 END) as upcoming_appointments
        FROM appointments
      `),
      
      // Atividade recente
      executeQuery(`
        SELECT 
          'users' as type,
          COUNT(*) as count,
          MAX(created_at) as last_activity
        FROM users 
        WHERE created_at >= NOW() - INTERVAL '24 hours'
        UNION ALL
        SELECT 
          'conversations' as type,
          COUNT(*) as count,
          MAX(created_at) as last_activity
        FROM conversations 
        WHERE created_at >= NOW() - INTERVAL '24 hours'
        UNION ALL
        SELECT 
          'messages' as type,
          COUNT(*) as count,
          MAX(created_at) as last_activity
        FROM messages 
        WHERE created_at >= NOW() - INTERVAL '24 hours'
        UNION ALL
        SELECT 
          'appointments' as type,
          COUNT(*) as count,
          MAX(created_at) as last_activity
        FROM appointments 
        WHERE created_at >= NOW() - INTERVAL '24 hours'
      `)
    ]);

    // Processar dados
    const users = usersStats[0] || {};
    const conversations = conversationsStats[0] || {};
    const messages = messagesStats[0] || {};
    const appointments = appointmentsStats[0] || {};

    // Calcular métricas derivadas
    const conversionRate = users.total_users > 0 ? 
      ((conversations.total_conversations / users.total_users) * 100).toFixed(1) : '0';
    
    const appointmentRate = users.total_users > 0 ? 
      ((appointments.total_appointments / users.total_users) * 100).toFixed(1) : '0';

    const avgMessagesPerConversation = conversations.total_conversations > 0 ? 
      (messages.total_messages / conversations.total_conversations).toFixed(1) : '0';

    // Processar atividade recente
    const recentActivityData = recentActivity.reduce((acc: any, item: any) => {
      acc[item.type] = {
        count: parseInt(item.count),
        last_activity: item.last_activity
      };
      return acc;
    }, {});

    const stats = {
      overview: {
        total_users: parseInt(users.total_users || 0),
        total_conversations: parseInt(conversations.total_conversations || 0),
        total_messages: parseInt(messages.total_messages || 0),
        total_appointments: parseInt(appointments.total_appointments || 0),
        conversion_rate: parseFloat(conversionRate),
        appointment_rate: parseFloat(appointmentRate),
        avg_messages_per_conversation: parseFloat(avgMessagesPerConversation)
      },
      users: {
        total: parseInt(users.total_users || 0),
        new_this_week: parseInt(users.new_users_week || 0),
        new_this_month: parseInt(users.new_users_month || 0),
        with_email: parseInt(users.users_with_email || 0),
        with_phone: parseInt(users.users_with_phone || 0),
        email_completion_rate: users.total_users > 0 ? 
          ((users.users_with_email / users.total_users) * 100).toFixed(1) : '0'
      },
      conversations: {
        total: parseInt(conversations.total_conversations || 0),
        new_this_week: parseInt(conversations.new_conversations_week || 0),
        active_24h: parseInt(conversations.active_conversations_24h || 0),
        active: parseInt(conversations.active_conversations || 0),
        closed: parseInt(conversations.closed_conversations || 0)
      },
      messages: {
        total: parseInt(messages.total_messages || 0),
        last_24h: parseInt(messages.messages_24h || 0),
        last_week: parseInt(messages.messages_week || 0),
        inbound: parseInt(messages.inbound_messages || 0),
        outbound: parseInt(messages.outbound_messages || 0)
      },
      appointments: {
        total: parseInt(appointments.total_appointments || 0),
        new_this_week: parseInt(appointments.new_appointments_week || 0),
        confirmed: parseInt(appointments.confirmed_appointments || 0),
        pending: parseInt(appointments.pending_appointments || 0),
        cancelled: parseInt(appointments.cancelled_appointments || 0),
        upcoming: parseInt(appointments.upcoming_appointments || 0)
      },
      recent_activity: recentActivityData,
      generated_at: new Date().toISOString()
    };

    console.log('✅ API: Estatísticas geradas com sucesso');
    return NextResponse.json({
      success: true,
      data: stats
    });

  } catch (error) {
    console.error('❌ API: Erro ao buscar estatísticas:', error);
    return NextResponse.json({
      success: false,
      error: 'Erro interno do servidor',
      details: error instanceof Error ? error.message : 'Erro desconhecido'
    }, { status: 500 });
  }
}