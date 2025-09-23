import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  try {
    // Extrair token do cookie
    const authToken = request.cookies.get('access_token')?.value;
    
    console.log('🔍 Debug Token - Token encontrado:', authToken ? 'Sim' : 'Não');
    
    if (authToken) {
      console.log('🔍 Token completo:', authToken);
      console.log('🔍 Token length:', authToken.length);
      console.log('🔍 Token primeiros 50 chars:', authToken.substring(0, 50));
      
      // Testar se o token funciona com Railway
      const testResponse = await fetch('https://wppagent-production.up.railway.app/admin/me', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
      });
      
      console.log('🧪 Teste Railway - Status:', testResponse.status);
      
      if (testResponse.ok) {
        const userData = await testResponse.json();
        console.log('✅ Token válido no Railway:', userData);
        
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
        console.log('❌ Token inválido no Railway:', errorText);
        
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
    console.error('❌ Erro no debug token:', error);
    return NextResponse.json({
      success: false,
      message: 'Erro interno',
      error: error instanceof Error ? error.message : 'Unknown error'
    });
  }
}
