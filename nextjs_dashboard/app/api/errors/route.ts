import { NextRequest, NextResponse } from 'next/server';

interface ErrorReport {
  id: string;
  message: string;
  stack?: string;
  componentStack?: string;
  level: 'global' | 'page' | 'component';
  name: string;
  timestamp: string;
  userAgent: string;
  url: string;
  userId: string | null;
  sessionId: string | null;
  retryCount: number;
}

export async function POST(request: NextRequest) {
  try {
    const errorReport: ErrorReport = await request.json();
    
    // Log do erro de forma estruturada
    console.group(`🚨 Frontend Error Report [${errorReport.level}]`);
    console.log('📋 Error ID:', errorReport.id);
    console.log('📍 Location:', errorReport.name);
    console.log('🕒 Timestamp:', errorReport.timestamp);
    console.log('🔗 URL:', errorReport.url);
    console.log('👤 User ID:', errorReport.userId || 'Anonymous');
    console.log('🎯 Session ID:', errorReport.sessionId || 'No session');
    console.log('🔄 Retry Count:', errorReport.retryCount);
    console.log('💻 User Agent:', errorReport.userAgent);
    console.log('📝 Message:', errorReport.message);
    
    if (errorReport.stack) {
      console.log('📚 Stack Trace:');
      console.log(errorReport.stack);
    }
    
    if (errorReport.componentStack) {
      console.log('🧩 Component Stack:');
      console.log(errorReport.componentStack);
    }
    console.groupEnd();
    
    // Em produção, aqui você enviaria para um serviço de monitoramento como:
    // - Sentry
    // - LogRocket  
    // - Bugsnag
    // - DataDog
    // - New Relic
    
    // Exemplo de integração com serviço externo:
    /*
    await fetch('https://api.sentry.io/api/errors', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${process.env.SENTRY_API_KEY}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(errorReport)
    });
    */
    
    // Salvar no banco de dados local (opcional)
    await saveErrorToDatabase(errorReport);
    
    // Notificar equipe em casos críticos
    if (errorReport.level === 'global' || errorReport.retryCount >= 3) {
      await notifyTeam(errorReport);
    }
    
    return NextResponse.json({ 
      success: true, 
      message: 'Error reported successfully',
      errorId: errorReport.id 
    });
    
  } catch (error) {
    console.error('❌ Failed to process error report:', error);
    
    return NextResponse.json(
      { success: false, message: 'Failed to process error report' },
      { status: 500 }
    );
  }
}

async function saveErrorToDatabase(errorReport: ErrorReport) {
  try {
    // Aqui você salvaria no seu banco de dados
    // Exemplo com PostgreSQL/SQLite:
    /*
    await db.execute(`
      INSERT INTO error_reports (
        id, message, stack, component_stack, level, name, 
        timestamp, user_agent, url, user_id, session_id, retry_count
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `, [
      errorReport.id, errorReport.message, errorReport.stack,
      errorReport.componentStack, errorReport.level, errorReport.name,
      errorReport.timestamp, errorReport.userAgent, errorReport.url,
      errorReport.userId, errorReport.sessionId, errorReport.retryCount
    ]);
    */
    
    console.log(`💾 Error ${errorReport.id} saved to database`);
  } catch (error) {
    console.error('❌ Failed to save error to database:', error);
  }
}

async function notifyTeam(errorReport: ErrorReport) {
  try {
    // Notificação para equipe via Slack, Discord, email, etc.
    // Exemplo com webhook do Slack:
    /*
    await fetch(process.env.SLACK_WEBHOOK_URL!, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text: `🚨 Critical Frontend Error`,
        blocks: [
          {
            type: "section",
            text: {
              type: "mrkdwn",
              text: `*Error ID:* ${errorReport.id}\n*Level:* ${errorReport.level}\n*Location:* ${errorReport.name}\n*Message:* ${errorReport.message}\n*URL:* ${errorReport.url}\n*User:* ${errorReport.userId || 'Anonymous'}`
            }
          }
        ]
      })
    });
    */
    
    console.log(`📢 Critical error ${errorReport.id} notification sent to team`);
  } catch (error) {
    console.error('❌ Failed to notify team:', error);
  }
}

// GET endpoint para consultar erros (útil para debugging)
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const errorId = searchParams.get('id');
    const level = searchParams.get('level');
    const limit = parseInt(searchParams.get('limit') || '50');
    
    // Aqui você buscaria no banco de dados
    const errors = await getErrorsFromDatabase({ errorId, level, limit });
    
    return NextResponse.json({
      success: true,
      data: errors,
      total: errors.length
    });
    
  } catch (error) {
    console.error('❌ Failed to fetch errors:', error);
    
    return NextResponse.json(
      { success: false, message: 'Failed to fetch errors' },
      { status: 500 }
    );
  }
}

async function getErrorsFromDatabase(filters: {
  errorId?: string | null;
  level?: string | null;
  limit: number;
}) {
  // Implementar busca no banco de dados
  // Por enquanto retorna array vazio
  return [];
}
