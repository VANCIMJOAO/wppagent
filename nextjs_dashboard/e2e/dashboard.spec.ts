import { test, expect } from '@playwright/test';

test.describe('Dashboard Authentication Flow', () => {
  test('should redirect to login when not authenticated', async ({ page }) => {
    await page.goto('/dashboard/dashboard');
    
    // Should be redirected to login page
    await expect(page).toHaveURL('/login');
  });

  test('should login and access dashboard', async ({ page }) => {
    await page.goto('/login');
    
    // Check if login form is present
    await expect(page.locator('form')).toBeVisible();
    
    // Fill in credentials (adjust selectors based on actual implementation)
    await page.fill('[data-testid="email"]', 'admin@test.com');
    await page.fill('[data-testid="password"]', 'admin123');
    
    // Submit login form
    await page.click('[data-testid="login-button"]');
    
    // Should be redirected to dashboard
    await expect(page).toHaveURL('/dashboard/dashboard');
    
    // Check if dashboard content is loaded
    await expect(page.locator('[data-testid="dashboard-stats"]')).toBeVisible();
  });

  test('should handle login errors gracefully', async ({ page }) => {
    await page.goto('/login');
    
    // Try to login with invalid credentials
    await page.fill('[data-testid="email"]', 'invalid@test.com');
    await page.fill('[data-testid="password"]', 'wrongpassword');
    await page.click('[data-testid="login-button"]');
    
    // Should show error message
    await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
    
    // Should remain on login page
    await expect(page).toHaveURL('/login');
  });

  test('should logout successfully', async ({ page }) => {
    // First login
    await page.goto('/login');
    await page.fill('[data-testid="email"]', 'admin@test.com');
    await page.fill('[data-testid="password"]', 'admin123');
    await page.click('[data-testid="login-button"]');
    
    // Wait for dashboard to load
    await expect(page).toHaveURL('/dashboard/dashboard');
    
    // Click logout button (adjust selector based on actual implementation)
    await page.click('[data-testid="logout-button"]');
    
    // Should be redirected to login
    await expect(page).toHaveURL('/login');
  });
});

test.describe('Dashboard Navigation', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('/login');
    await page.fill('[data-testid="email"]', 'admin@test.com');
    await page.fill('[data-testid="password"]', 'admin123');
    await page.click('[data-testid="login-button"]');
    await expect(page).toHaveURL('/dashboard/dashboard');
  });

  test('should navigate to clients page', async ({ page }) => {
    await page.click('[data-testid="clients-nav"]');
    
    // Should navigate to clients page
    await expect(page).toHaveURL('/dashboard/clientes');
    
    // Check if clients table is visible
    await expect(page.locator('[data-testid="clients-table"]')).toBeVisible();
  });

  test('should navigate to appointments page', async ({ page }) => {
    await page.click('[data-testid="appointments-nav"]');
    
    // Should navigate to appointments page
    await expect(page).toHaveURL('/dashboard/agendamentos');
    
    // Check if appointments content is visible
    await expect(page.locator('[data-testid="appointments-content"]')).toBeVisible();
  });

  test('should navigate to conversations page', async ({ page }) => {
    await page.click('[data-testid="conversations-nav"]');
    
    // Should navigate to conversations page
    await expect(page).toHaveURL('/dashboard/conversas');
    
    // Check if conversations content is visible
    await expect(page.locator('[data-testid="conversations-content"]')).toBeVisible();
  });
});

test.describe('Dashboard Functionality', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('/login');
    await page.fill('[data-testid="email"]', 'admin@test.com');
    await page.fill('[data-testid="password"]', 'admin123');
    await page.click('[data-testid="login-button"]');
    await expect(page).toHaveURL('/dashboard/dashboard');
  });

  test('should load dashboard stats', async ({ page }) => {
    // Check if all stat cards are visible
    await expect(page.locator('[data-testid="total-clients-stat"]')).toBeVisible();
    await expect(page.locator('[data-testid="total-conversations-stat"]')).toBeVisible();
    await expect(page.locator('[data-testid="total-appointments-stat"]')).toBeVisible();
    await expect(page.locator('[data-testid="total-messages-stat"]')).toBeVisible();
    
    // Stats should contain numbers (not loading states)
    await expect(page.locator('[data-testid="total-clients-stat"] .stat-value')).not.toContainText('Carregando');
  });

  test('should search clients', async ({ page }) => {
    // Navigate to clients page
    await page.click('[data-testid="clients-nav"]');
    await expect(page).toHaveURL('/dashboard/clientes');
    
    // Wait for clients table to load
    await expect(page.locator('[data-testid="clients-table"]')).toBeVisible();
    
    // Search for a specific client
    await page.fill('[data-testid="client-search"]', 'João');
    
    // Results should be filtered
    await expect(page.locator('[data-testid="client-row"]')).toContainText('João');
  });

  test('should handle error states gracefully', async ({ page }) => {
    // Mock network failure
    await page.route('**/api/dashboard/stats/daily', route => {
      route.abort('failed');
    });
    
    // Reload page to trigger error
    await page.reload();
    
    // Should show error state or fallback content
    await expect(page.locator('[data-testid="error-boundary"]')).toBeVisible();
  });

  test('should be responsive on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Dashboard should be responsive
    await expect(page.locator('[data-testid="dashboard-stats"]')).toBeVisible();
    
    // Sidebar should be collapsible on mobile
    const sidebar = page.locator('[data-testid="sidebar"]');
    if (await sidebar.isVisible()) {
      // Check if hamburger menu is present
      await expect(page.locator('[data-testid="mobile-menu-button"]')).toBeVisible();
    }
  });
});
