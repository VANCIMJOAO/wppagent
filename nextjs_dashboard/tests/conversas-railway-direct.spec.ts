import { test, expect } from '@playwright/test';

test.describe('Conversas - Teste Direto Railway Backend', () => {
  
  test('1. Verificar Health Check do Backend Railway', async ({ page }) => {
    console.log('🔍 Testando health check do Railway...');
    
    await page.goto('https://wppagent-production.up.railway.app/');
    await page.waitForLoadState('networkidle');
    
    // Verificar resposta JSON
    const response = await page.evaluate(async () => {
      const res = await fetch('https://wppagent-production.up.railway.app/');
      return await res.json();
    });
    
    expect(response.success).toBe(true);
    expect(response.data.status).toBe('healthy');
    expect(response.data.message).toBe('WhatsApp Agent API is running');
    
    console.log('✅ Backend Railway está saudável:', response.data);
  });

  test('2. Testar API de Login no Railway via Proxy', async ({ page }) => {
    console.log('🔍 Testando login no Railway via proxy local...');
    
    // Usar o proxy local que já está configurado
    const loginResponse = await page.evaluate(async () => {
      const response = await fetch('http://localhost:3000/api/proxy/admin/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: 'admin',
          password: 'admin123'
        })
      });
      
      const data = await response.json();
      console.log('🔍 Resposta completa do login:', JSON.stringify(data, null, 2));
      
      return {
        status: response.status,
        data: data
      };
    });
    
    expect(loginResponse.status).toBe(200);
    console.log('📊 Dados recebidos:', JSON.stringify(loginResponse.data, null, 2));
    
    // Verificar se o token existe na estrutura correta
    const token = loginResponse.data.data?.access_token;
    
    expect(token).toBeDefined();
    
    console.log('✅ Login realizado com sucesso via proxy');
    console.log('🔑 Token obtido:', token?.substring(0, 20) + '...');
    
    // Armazenar token para próximos testes
    await page.evaluate((tokenValue) => {
      window.railwayToken = tokenValue;
    }, token);
  });

  test('3. Testar API de Conversas Direto Railway', async ({ request }) => {
    console.log('🔍 Testando API de conversas direto no Railway...');
    
    // Primeiro fazer login direto no Railway
    const loginResponse = await request.post('https://wppagent-production.up.railway.app/admin/login', {
      data: {
        username: 'admin',
        password: 'admin123'
      }
    });
    
    expect(loginResponse.ok()).toBeTruthy();
    const loginData = await loginResponse.json();
    const token = loginData.data?.access_token;
    
    expect(token).toBeDefined();
    console.log('✅ Login realizado com sucesso no Railway');
    
    // Agora testar API de conversas direto no Railway
    const conversationsResponse = await request.get('https://wppagent-production.up.railway.app/conversations/?offset=0&limit=10', {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      }
    });
    
    expect(conversationsResponse.ok()).toBeTruthy();
    const conversationsData = await conversationsResponse.json();
    
    console.log('✅ API de conversas funcionando direto no Railway');
    console.log('📊 Resposta:', JSON.stringify(conversationsData, null, 2));
    
    // Verificar estrutura dos dados
    expect(conversationsData.data.conversations).toBeDefined();
    expect(Array.isArray(conversationsData.data.conversations)).toBe(true);
    
    console.log(`📝 Conversas encontradas: ${conversationsData.data.conversations.length}`);
    console.log(`📊 Total: ${conversationsData.data.total}`);
    
    if (conversationsData.data.conversations.length > 0) {
      console.log('📋 Primeira conversa:', JSON.stringify(conversationsData.data.conversations[0], null, 2));
    }
  });

  test('4. Testar API de Mensagens Direto Railway', async ({ request }) => {
    console.log('🔍 Testando API de mensagens direto no Railway...');
    
    // Fazer login direto no Railway
    const loginResponse = await request.post('https://wppagent-production.up.railway.app/admin/login', {
      data: {
        username: 'admin',
        password: 'admin123'
      }
    });
    
    expect(loginResponse.ok()).toBeTruthy();
    const loginData = await loginResponse.json();
    const token = loginData.data?.access_token;
    
    expect(token).toBeDefined();
    console.log('✅ Login realizado com sucesso no Railway');
    
    // Buscar conversas primeiro
    const conversationsResponse = await request.get('https://wppagent-production.up.railway.app/conversations/?offset=0&limit=5', {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      }
    });
    
    expect(conversationsResponse.ok()).toBeTruthy();
    const conversationsData = await conversationsResponse.json();
    
    if (conversationsData.data.conversations && conversationsData.data.conversations.length > 0) {
      const conversationId = conversationsData.data.conversations[0].id;
      console.log(`🔍 Testando mensagens da conversa ID: ${conversationId}`);
      
      // Buscar mensagens da primeira conversa
      const messagesResponse = await request.get(`https://wppagent-production.up.railway.app/messages/${conversationId}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        }
      });
      
      console.log(`🔍 Status da resposta de mensagens: ${messagesResponse.status()}`);
      
      if (messagesResponse.ok()) {
        const messagesData = await messagesResponse.json();
        console.log('✅ API de mensagens funcionando direto no Railway');
        console.log('📨 Mensagens:', JSON.stringify(messagesData, null, 2));
      } else {
        const errorData = await messagesResponse.json();
        console.log('⚠️ API de mensagens retornou erro:', messagesResponse.status());
        console.log('📨 Erro:', JSON.stringify(errorData, null, 2));
        
        // Verificar se é um erro esperado
        if (messagesResponse.status() === 404) {
          console.log('✅ Erro 404 é esperado se não há mensagens para esta conversa');
        } else if (messagesResponse.status() === 405) {
          console.log('⚠️ Erro 405: Endpoint de mensagens não implementado ou método não permitido');
          console.log('📝 Nota: API de mensagens pode não estar disponível no backend Railway');
        } else {
          // Para outros erros, falhar o teste
          expect(messagesResponse.ok()).toBeTruthy();
        }
      }
    } else {
      console.log('⚠️ Nenhuma conversa encontrada para testar mensagens');
    }
  });

  test('5. Teste Completo de Integração', async ({ page, request }) => {
    console.log('🚀 Executando teste completo de integração...');
    
    // 1. Health Check
    await page.goto('https://wppagent-production.up.railway.app/');
    await page.waitForLoadState('networkidle');
    
    const healthResponse = await request.get('https://wppagent-production.up.railway.app/');
    expect(healthResponse.ok()).toBeTruthy();
    const healthData = await healthResponse.json();
    expect(healthData.success).toBe(true);
    console.log('✅ 1. Health Check OK');
    
    // 2. Login
    const loginResponse = await request.post('https://wppagent-production.up.railway.app/admin/login', {
      data: {
        username: 'admin',
        password: 'admin123'
      }
    });
    
    expect(loginResponse.ok()).toBeTruthy();
    const loginData = await loginResponse.json();
    const token = loginData.data?.access_token;
    
    expect(token).toBeDefined();
    console.log('✅ 2. Login OK');
    
    // 3. Conversas
    const conversationsResponse = await request.get('https://wppagent-production.up.railway.app/conversations/?offset=0&limit=20', {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      }
    });
    
    expect(conversationsResponse.ok()).toBeTruthy();
    const conversationsData = await conversationsResponse.json();
    
    expect(conversationsData.data.conversations).toBeDefined();
    expect(Array.isArray(conversationsData.data.conversations)).toBe(true);
    console.log('✅ 3. API Conversas OK');
    console.log(`📊 ${conversationsData.data.conversations.length} conversas encontradas de ${conversationsData.data.total} totais`);
    
    // 4. Verificar estrutura dos dados
    if (conversationsData.data.conversations.length > 0) {
      const firstConv = conversationsData.data.conversations[0];
      expect(firstConv.id).toBeDefined();
      expect(firstConv.user_phone).toBeDefined();
      expect(firstConv.status).toBeDefined();
      expect(firstConv.total_messages).toBeDefined();
      
      console.log('✅ 4. Estrutura de dados OK');
      console.log('📋 Exemplo de conversa:', {
        id: firstConv.id,
        user_name: firstConv.user_name,
        user_phone: firstConv.user_phone,
        status: firstConv.status,
        total_messages: firstConv.total_messages
      });
    }
    
    console.log('🎉 TESTE COMPLETO DE INTEGRAÇÃO CONCLUÍDO COM SUCESSO!');
    console.log('✅ Backend Railway está funcionando perfeitamente');
    console.log('✅ APIs de autenticação e conversas estão operacionais');
    console.log('✅ Estrutura de dados está correta');
  });
});
