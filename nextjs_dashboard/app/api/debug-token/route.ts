import { NextRequest, NextResponse } from 'next/server';
import { debugLog } from '@/lib/debug';

export async function GET(request: NextRequest) {
  try {
    // Extrair token do cookie
    const authToken = request.cookies.get('access_token')?.value;
    
    debugLog.info('🔍 Debug Token - Token encontrado:', authToken ? 'Sim' : 'Não');
    
    if (authToken) {
      debugLog.info('🔍 Token completo:', authToken);
      debugLog.info('🔍 Token length:', authToken.length);
      debugLog.info('🔍 Token primeiros 50 chars:', authToken.substring(0, 50));
      
      // Testar se o token funciona com Railway
      const testResponse = await fetch('https://wppagent-production.up.railway.app/admin/me', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
      });
      
      debugLog.info('🧪 Teste Railway - Status:', testResponse.status);
      
      if (testResponse.ok) {
        const userData = await testResponse.json();
        debugLog.success('Token válido no Railway:', userData);
        
        // Testar também o endpoint de conversas
        const conversationsResponse = await fetch('https://wppagent-production.up.railway.app/conversations?limit=5', {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${authToken}`,
            'Content-Type': 'application/json',
          },
        });
        
        let conversationsTest = 'FAILED';
        let conversationsData = null;
        
        if (conversationsResponse.ok) {
          conversationsData = await conversationsResponse.json();
          conversationsTest = 'SUCCESS';
        } else {
          const conversationsError = await conversationsResponse.text();
          conversationsData = { error: conversationsError, status: conversationsResponse.status };
        }
        
        return NextResponse.json({
          success: true,
          message: 'Token válido',
          tokenPresent: true,
          tokenLength: authToken.length,
          railwayTest: 'SUCCESS',
          userData: userData,
          conversationsTest: conversationsTest,
          conversationsData: conversationsData
        });
      } else {
        const errorText = await testResponse.text();
        debugLog.error('Token inválido no Railway:', errorText);
        
        return NextResponse.json({
          success: false,
          message: 'Token inválido no Railway',
          tokenPresent: true,
          tokenLength: authToken.length,
          railwayTest: 'FAILED',
          railwayError: errorText
        });
      }
    }
    
    return NextResponse.json({
      success: false,
      message: 'Token não encontrado',
      tokenPresent: false
    });
    
  } catch (error) {
    debugLog.error('Erro no debug token:', error);
    return NextResponse.json({
      success: false,
      message: 'Erro interno',
      error: error instanceof Error ? error.message : 'Unknown error'
    });
  }
}
