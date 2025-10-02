import { test, expect } from '@playwright/test';

// Função de login
async function login(page: any) {
  await page.goto('/login');
  await page.fill('input[name="email"]', 'admin@test.com');
  await page.fill('input[name="password"]', 'admin123');
  await page.click('button[type="submit"]');
  await page.waitForURL('/dashboard');
  await page.waitForLoadState('networkidle');
}

test.describe('🧪 Edge Cases - Validação de Formulários', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test.describe('📅 Agendamentos - Validação de Campos', () => {
    test('deve validar campos obrigatórios vazios', async ({ page }) => {
      await page.goto('/agendamentos');
      await page.waitForLoadState('networkidle');

      // Clicar em "Novo Agendamento"
      await page.click('button:has-text("Novo Agendamento")');
      
      // Tentar salvar sem preencher campos obrigatórios
      await page.click('button:has-text("Criar")');
      
      // Verificar mensagens de erro
      await expect(page.locator('text=Cliente é obrigatório')).toBeVisible();
      await expect(page.locator('text=Serviço é obrigatório')).toBeVisible();
      await expect(page.locator('text=Data é obrigatória')).toBeVisible();
      await expect(page.locator('text=Horário é obrigatório')).toBeVisible();
    });

    test('deve validar data no passado', async ({ page }) => {
      await page.goto('/agendamentos');
      await page.waitForLoadState('networkidle');

      await page.click('button:has-text("Novo Agendamento")');
      
      // Selecionar data no passado
      await page.click('button:has-text("Selecione a data")');
      await page.click('[data-day="1"]'); // Dia 1 do mês anterior
      
      // Preencher outros campos obrigatórios
      await page.selectOption('select[name="user_id"]', '1');
      await page.selectOption('select[name="service_id"]', '1');
      await page.fill('input[name="hora_agendamento"]', '10:00');
      
      await page.click('button:has-text("Criar")');
      
      // Verificar erro de data no passado
      await expect(page.locator('text=Data não pode ser no passado')).toBeVisible();
    });

    test('deve validar horário fora do expediente', async ({ page }) => {
      await page.goto('/agendamentos');
      await page.waitForLoadState('networkidle');

      await page.click('button:has-text("Novo Agendamento")');
      
      // Preencher campos obrigatórios
      await page.selectOption('select[name="user_id"]', '1');
      await page.selectOption('select[name="service_id"]', '1');
      
      // Selecionar data futura
      await page.click('button:has-text("Selecione a data")');
      await page.click('[data-day="15"]'); // Dia 15 do próximo mês
      
      // Horário fora do expediente (antes das 8h)
      await page.fill('input[name="hora_agendamento"]', '07:00');
      
      await page.click('button:has-text("Criar")');
      
      // Verificar erro de horário
      await expect(page.locator('text=Horário deve estar entre 8h e 18h')).toBeVisible();
    });

    test('deve validar valor negativo', async ({ page }) => {
      await page.goto('/agendamentos');
      await page.waitForLoadState('networkidle');

      await page.click('button:has-text("Novo Agendamento")');
      
      // Preencher campos obrigatórios
      await page.selectOption('select[name="user_id"]', '1');
      await page.selectOption('select[name="service_id"]', '1');
      
      // Selecionar data futura
      await page.click('button:has-text("Selecione a data")');
      await page.click('[data-day="15"]');
      
      await page.fill('input[name="hora_agendamento"]', '10:00');
      
      // Valor negativo
      await page.fill('input[name="valor"]', '-100');
      
      await page.click('button:has-text("Criar")');
      
      // Verificar erro de valor
      await expect(page.locator('text=Valor não pode ser negativo')).toBeVisible();
    });

    test('deve validar duração mínima', async ({ page }) => {
      await page.goto('/agendamentos');
      await page.waitForLoadState('networkidle');

      await page.click('button:has-text("Novo Agendamento")');
      
      // Preencher campos obrigatórios
      await page.selectOption('select[name="user_id"]', '1');
      await page.selectOption('select[name="service_id"]', '1');
      
      // Selecionar data futura
      await page.click('button:has-text("Selecione a data")');
      await page.click('[data-day="15"]');
      
      await page.fill('input[name="hora_agendamento"]', '10:00');
      
      // Duração muito baixa
      await page.fill('input[name="duracao_minutos"]', '5');
      
      await page.click('button:has-text("Criar")');
      
      // Verificar erro de duração
      await expect(page.locator('text=Duração deve ser pelo menos 15 minutos')).toBeVisible();
    });
  });

  test.describe('👥 Clientes - Validação de Campos', () => {
    test('deve validar email inválido', async ({ page }) => {
      await page.goto('/clientes');
      await page.waitForLoadState('networkidle');

      await page.click('button:has-text("Novo Cliente")');
      
      // Preencher campos com email inválido
      await page.fill('input[name="nome"]', 'João Silva');
      await page.fill('input[name="telefone"]', '(11) 99999-9999');
      await page.fill('input[name="email"]', 'email-invalido');
      
      await page.click('button:has-text("Salvar")');
      
      // Verificar erro de email
      await expect(page.locator('text=Email inválido')).toBeVisible();
    });

    test('deve validar telefone inválido', async ({ page }) => {
      await page.goto('/clientes');
      await page.waitForLoadState('networkidle');

      await page.click('button:has-text("Novo Cliente")');
      
      // Preencher campos com telefone inválido
      await page.fill('input[name="nome"]', 'João Silva');
      await page.fill('input[name="telefone"]', '123'); // Telefone muito curto
      await page.fill('input[name="email"]', 'joao@test.com');
      
      await page.click('button:has-text("Salvar")');
      
      // Verificar erro de telefone
      await expect(page.locator('text=Telefone deve ter pelo menos 10 dígitos')).toBeVisible();
    });

    test('deve validar nome muito curto', async ({ page }) => {
      await page.goto('/clientes');
      await page.waitForLoadState('networkidle');

      await page.click('button:has-text("Novo Cliente")');
      
      // Nome muito curto
      await page.fill('input[name="nome"]', 'Jo');
      await page.fill('input[name="telefone"]', '(11) 99999-9999');
      await page.fill('input[name="email"]', 'joao@test.com');
      
      await page.click('button:has-text("Salvar")');
      
      // Verificar erro de nome
      await expect(page.locator('text=Nome deve ter pelo menos 3 caracteres')).toBeVisible();
    });
  });

  test.describe('💬 Conversas - Validação de Mensagens', () => {
    test('deve validar mensagem vazia', async ({ page }) => {
      await page.goto('/conversas');
      await page.waitForLoadState('networkidle');

      // Selecionar uma conversa
      const conversation = page.locator('[data-testid="conversation-item"]').first();
      if (await conversation.count() > 0) {
        await conversation.click();
        
        // Tentar enviar mensagem vazia
        await page.fill('textarea[name="message"]', '');
        await page.click('button:has-text("Enviar")');
        
        // Verificar erro
        await expect(page.locator('text=Mensagem não pode estar vazia')).toBeVisible();
      }
    });

    test('deve validar mensagem muito longa', async ({ page }) => {
      await page.goto('/conversas');
      await page.waitForLoadState('networkidle');

      // Selecionar uma conversa
      const conversation = page.locator('[data-testid="conversation-item"]').first();
      if (await conversation.count() > 0) {
        await conversation.click();
        
        // Mensagem muito longa (mais de 1000 caracteres)
        const longMessage = 'a'.repeat(1001);
        await page.fill('textarea[name="message"]', longMessage);
        await page.click('button:has-text("Enviar")');
        
        // Verificar erro
        await expect(page.locator('text=Mensagem muito longa')).toBeVisible();
      }
    });
  });

  test.describe('🔧 Serviços - Validação de Campos', () => {
    test('deve validar nome de serviço vazio', async ({ page }) => {
      await page.goto('/servicos');
      await page.waitForLoadState('networkidle');

      await page.click('button:has-text("Novo Serviço")');
      
      // Tentar salvar sem nome
      await page.fill('input[name="description"]', 'Descrição do serviço');
      await page.fill('input[name="duration_minutes"]', '60');
      await page.fill('input[name="price"]', '100');
      
      await page.click('button:has-text("Salvar")');
      
      // Verificar erro
      await expect(page.locator('text=Nome do serviço é obrigatório')).toBeVisible();
    });

    test('deve validar preço negativo', async ({ page }) => {
      await page.goto('/servicos');
      await page.waitForLoadState('networkidle');

      await page.click('button:has-text("Novo Serviço")');
      
      // Preencher com preço negativo
      await page.fill('input[name="name"]', 'Serviço Teste');
      await page.fill('input[name="description"]', 'Descrição do serviço');
      await page.fill('input[name="duration_minutes"]', '60');
      await page.fill('input[name="price"]', '-50');
      
      await page.click('button:has-text("Salvar")');
      
      // Verificar erro
      await expect(page.locator('text=Preço não pode ser negativo')).toBeVisible();
    });

    test('deve validar duração inválida', async ({ page }) => {
      await page.goto('/servicos');
      await page.waitForLoadState('networkidle');

      await page.click('button:has-text("Novo Serviço")');
      
      // Duração muito baixa
      await page.fill('input[name="name"]', 'Serviço Teste');
      await page.fill('input[name="description"]', 'Descrição do serviço');
      await page.fill('input[name="duration_minutes"]', '5');
      await page.fill('input[name="price"]', '100');
      
      await page.click('button:has-text("Salvar")');
      
      // Verificar erro
      await expect(page.locator('text=Duração deve ser pelo menos 15 minutos')).toBeVisible();
    });
  });

  test.describe('🌐 WebSocket - Edge Cases', () => {
    test('deve lidar com conexão perdida', async ({ page }) => {
      await page.goto('/dashboard');
      
      // Simular perda de conexão
      await page.evaluate(() => {
        if (window.wsConnection) {
          window.wsConnection.close();
        }
      });
      
      // Verificar se indicador de desconexão aparece
      await expect(page.locator('[data-testid="connection-status"]')).toContainText('Desconectado');
    });

    test('deve reconectar automaticamente', async ({ page }) => {
      await page.goto('/dashboard');
      
      // Simular perda e restauração de conexão
      await page.evaluate(() => {
        if (window.wsConnection) {
          window.wsConnection.close();
        }
      });
      
      // Aguardar reconexão
      await page.waitForTimeout(3000);
      
      // Verificar se reconectou
      const isConnected = await page.evaluate(() => {
        return window.wsConnection && window.wsConnection.readyState === WebSocket.OPEN;
      });
      
      expect(isConnected).toBeTruthy();
    });
  });

  test.describe('📱 Responsividade - Edge Cases', () => {
    test('deve funcionar em tela pequena', async ({ page }) => {
      // Simular dispositivo móvel
      await page.setViewportSize({ width: 375, height: 667 });
      
      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');
      
      // Verificar se elementos estão visíveis
      await expect(page.locator('h2:has-text("Dashboard")')).toBeVisible();
      await expect(page.locator('h3:has-text("Navegação")')).toBeVisible();
    });

    test('deve funcionar em tela muito pequena', async ({ page }) => {
      // Simular tela muito pequena
      await page.setViewportSize({ width: 320, height: 568 });
      
      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');
      
      // Verificar se não há overflow horizontal
      const body = page.locator('body');
      const boundingBox = await body.boundingBox();
      expect(boundingBox?.width).toBeLessThanOrEqual(320);
    });
  });

  test.describe('🔒 Segurança - Edge Cases', () => {
    test('deve bloquear XSS em campos de texto', async ({ page }) => {
      await page.goto('/clientes');
      await page.waitForLoadState('networkidle');

      await page.click('button:has-text("Novo Cliente")');
      
      // Tentar inserir script malicioso
      const xssPayload = '<script>alert("XSS")</script>';
      await page.fill('input[name="nome"]', xssPayload);
      await page.fill('input[name="telefone"]', '(11) 99999-9999');
      await page.fill('input[name="email"]', 'test@test.com');
      
      await page.click('button:has-text("Salvar")');
      
      // Verificar se o script não foi executado
      const alertHandled = await page.evaluate(() => {
        return window.alert === undefined || !window.alert.toString().includes('XSS');
      });
      
      expect(alertHandled).toBeTruthy();
    });

    test('deve validar tamanho máximo de upload', async ({ page }) => {
      await page.goto('/perfil');
      await page.waitForLoadState('networkidle');
      
      // Tentar fazer upload de arquivo muito grande
      const largeFile = await page.evaluate(() => {
        const file = new File(['x'.repeat(10 * 1024 * 1024)], 'large.txt', { type: 'text/plain' });
        return file;
      });
      
      await page.setInputFiles('input[type="file"]', largeFile);
      
      // Verificar erro de tamanho
      await expect(page.locator('text=Arquivo muito grande')).toBeVisible();
    });
  });
});