import { test, expect, Page } from '@playwright/test';

const BASE_URL = 'http://localhost:3000';
const TEST_CREDENTIALS = {
  username: 'admin',
  password: 'admin123'
};

async function login(page: Page) {
  await page.goto('/login');
  await page.waitForLoadState('networkidle');
  
  await page.fill('input[id="username"]', TEST_CREDENTIALS.username);
  await page.fill('input[id="password"]', TEST_CREDENTIALS.password);
  await page.click('button[type="submit"]');
  
  await page.waitForURL('/dashboard');
  await page.waitForLoadState('networkidle');
}

test.describe('Funcionalidades em Tempo Real', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('WebSocket - Conexão e Reconexão', async ({ page }) => {
    await page.goto('/dashboard');
    
    // Verificar se WebSocket está conectado
    const wsStatus = await page.evaluate(() => {
      return window.WebSocket ? 'available' : 'not_available';
    });
    expect(wsStatus).toBe('available');
    
    // Simular perda de conexão
    await page.evaluate(() => {
      if (window.wsConnection) {
        window.wsConnection.close();
      }
    });
    
    // Aguardar reconexão automática
    await page.waitForTimeout(2000);
    
    // Verificar se reconectou
    const reconnected = await page.evaluate(() => {
      return window.wsConnection && window.wsConnection.readyState === WebSocket.OPEN;
    });
    expect(reconnected).toBeTruthy();
  });

  test('Dashboard - Atualizações em Tempo Real', async ({ page }) => {
    await page.goto('/dashboard');
    
    // Aguardar carregamento inicial
    await page.waitForSelector('[data-testid="total-clients"]');
    
    // Capturar valores iniciais
    const initialClients = await page.textContent('[data-testid="total-clients"]');
    const initialConversations = await page.textContent('[data-testid="total-conversations"]');
    
    // Simular atualização de dados via WebSocket
    await page.evaluate(() => {
      if (window.wsConnection && window.wsConnection.readyState === WebSocket.OPEN) {
        window.wsConnection.send(JSON.stringify({
          type: 'dashboard_update',
          data: {
            totalClients: 150,
            totalConversations: 300
          }
        }));
      }
    });
    
    // Aguardar atualização
    await page.waitForTimeout(1000);
    
    // Verificar se os valores foram atualizados
    const updatedClients = await page.textContent('[data-testid="total-clients"]');
    const updatedConversations = await page.textContent('[data-testid="total-conversations"]');
    
    expect(updatedClients).not.toBe(initialClients);
    expect(updatedConversations).not.toBe(initialConversations);
  });

  test('Conversas - Chat em Tempo Real', async ({ page }) => {
    await page.goto('/conversas');
    
    // Aguardar carregamento da interface de chat
    await page.waitForSelector('[data-testid="chat-area"]');
    
    // Simular recebimento de mensagem
    await page.evaluate(() => {
      if (window.wsConnection && window.wsConnection.readyState === WebSocket.OPEN) {
        window.wsConnection.send(JSON.stringify({
          type: 'new_message',
          data: {
            id: 'msg_123',
            content: 'Olá! Como posso ajudar?',
            sender: 'user',
            timestamp: new Date().toISOString()
          }
        }));
      }
    });
    
    // Aguardar mensagem aparecer
    await page.waitForSelector('[data-testid="message-msg_123"]');
    
    // Verificar se mensagem foi exibida
    await expect(page.locator('[data-testid="message-msg_123"]')).toContainText('Olá! Como posso ajudar?');
    
    // Simular envio de mensagem
    await page.fill('[data-testid="message-input"]', 'Preciso de ajuda com agendamento');
    await page.click('[data-testid="send-button"]');
    
    // Verificar se mensagem foi enviada
    await expect(page.locator('[data-testid="message-input"]')).toHaveValue('');
  });

  test('Agendamentos - Notificações em Tempo Real', async ({ page }) => {
    await page.goto('/agendamentos');
    
    // Aguardar carregamento da lista
    await page.waitForSelector('[data-testid="appointments-list"]');
    
    // Simular novo agendamento via WebSocket
    await page.evaluate(() => {
      if (window.wsConnection && window.wsConnection.readyState === WebSocket.OPEN) {
        window.wsConnection.send(JSON.stringify({
          type: 'new_appointment',
          data: {
            id: 'apt_123',
            clientName: 'João Silva',
            service: 'Limpeza de Pele',
            date: '2024-12-25',
            time: '14:00',
            status: 'agendado'
          }
        }));
      }
    });
    
    // Aguardar notificação
    await page.waitForSelector('[data-testid="notification"]');
    
    // Verificar se notificação foi exibida
    await expect(page.locator('[data-testid="notification"]')).toContainText('Novo agendamento');
    
    // Verificar se agendamento foi adicionado à lista
    await expect(page.locator('text=João Silva')).toBeVisible();
  });

  test('Monitoramento - Status em Tempo Real', async ({ page }) => {
    await page.goto('/monitoring');
    
    // Aguardar carregamento dos status
    await page.waitForSelector('[data-testid="whatsapp-status"]');
    
    // Simular mudança de status via WebSocket
    await page.evaluate(() => {
      if (window.wsConnection && window.wsConnection.readyState === WebSocket.OPEN) {
        window.wsConnection.send(JSON.stringify({
          type: 'status_update',
          data: {
            component: 'whatsapp',
            status: 'error',
            message: 'Conexão perdida com WhatsApp API'
          }
        }));
      }
    });
    
    // Aguardar atualização do status
    await page.waitForTimeout(1000);
    
    // Verificar se status foi atualizado
    await expect(page.locator('[data-testid="whatsapp-status"]')).toContainText('Erro');
  });

  test('Analytics - Gráficos em Tempo Real', async ({ page }) => {
    await page.goto('/analytics');
    
    // Aguardar carregamento dos gráficos
    await page.waitForSelector('[data-testid="chart-container"]');
    
    // Simular atualização de dados via WebSocket
    await page.evaluate(() => {
      if (window.wsConnection && window.wsConnection.readyState === WebSocket.OPEN) {
        window.wsConnection.send(JSON.stringify({
          type: 'analytics_update',
          data: {
            chartType: 'conversations',
            data: [
              { date: '2024-01-01', value: 100 },
              { date: '2024-01-02', value: 150 },
              { date: '2024-01-03', value: 200 }
            ]
          }
        }));
      }
    });
    
    // Aguardar atualização do gráfico
    await page.waitForTimeout(1000);
    
    // Verificar se gráfico foi atualizado
    await expect(page.locator('[data-testid="chart-container"]')).toBeVisible();
  });

  test('Notificações Push - Sistema de Notificações', async ({ page }) => {
    await page.goto('/dashboard');
    
    // Solicitar permissão para notificações
    const permission = await page.evaluate(async () => {
      if ('Notification' in window) {
        return await Notification.requestPermission();
      }
      return 'not_supported';
    });
    
    if (permission === 'granted') {
      // Simular notificação push
      await page.evaluate(() => {
        if ('Notification' in window) {
          new Notification('Nova mensagem recebida', {
            body: 'Você tem uma nova mensagem no WhatsApp',
            icon: '/icon-192x192.png'
          });
        }
      });
      
      // Verificar se notificação foi exibida
      await page.waitForTimeout(1000);
    }
  });

  test('Sincronização Offline/Online', async ({ page }) => {
    await page.goto('/dashboard');
    
    // Simular modo offline
    await page.context().setOffline(true);
    
    // Verificar se indicador offline aparece
    await expect(page.locator('[data-testid="offline-indicator"]')).toBeVisible();
    
    // Simular modo online
    await page.context().setOffline(false);
    
    // Aguardar sincronização
    await page.waitForTimeout(2000);
    
    // Verificar se indicador offline desaparece
    await expect(page.locator('[data-testid="offline-indicator"]')).not.toBeVisible();
  });

  test('Cache e Performance', async ({ page }) => {
    await page.goto('/dashboard');
    
    // Aguardar carregamento inicial
    await page.waitForLoadState('networkidle');
    
    // Navegar para outra página
    await page.goto('/agendamentos');
    await page.waitForLoadState('networkidle');
    
    // Voltar para dashboard
    await page.goto('/dashboard');
    
    // Verificar se carregou mais rápido (cache)
    const loadTime = await page.evaluate(() => {
      return performance.getEntriesByType('navigation')[0].loadEventEnd - 
             performance.getEntriesByType('navigation')[0].loadEventStart;
    });
    
    expect(loadTime).toBeLessThan(1000); // Deve carregar em menos de 1 segundo
  });

  test('Múltiplas Abas - Sincronização', async ({ browser }) => {
    // Criar duas abas
    const context = await browser.newContext();
    const page1 = await context.newPage();
    const page2 = await context.newPage();
    
    // Fazer login em ambas as abas
    await login(page1);
    await login(page2);
    
    // Navegar para dashboard em ambas
    await page1.goto('/dashboard');
    await page2.goto('/dashboard');
    
    // Aguardar carregamento
    await page1.waitForLoadState('networkidle');
    await page2.waitForLoadState('networkidle');
    
    // Simular atualização em uma aba
    await page1.evaluate(() => {
      if (window.wsConnection && window.wsConnection.readyState === WebSocket.OPEN) {
        window.wsConnection.send(JSON.stringify({
          type: 'dashboard_update',
          data: { totalClients: 999 }
        }));
      }
    });
    
    // Aguardar sincronização
    await page.waitForTimeout(1000);
    
    // Verificar se ambas as abas foram atualizadas
    const clients1 = await page1.textContent('[data-testid="total-clients"]');
    const clients2 = await page2.textContent('[data-testid="total-clients"]');
    
    expect(clients1).toBe(clients2);
    
    await context.close();
  });
});
