import { test, expect } from '@playwright/test';

test.describe('Smoke Tests @smoke', () => {
  test('should load homepage', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/Educational RPG/);
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
  });

  test('should load login page', async ({ page }) => {
    await page.goto('/login');
    await expect(page.getByRole('heading', { name: /로그인/i })).toBeVisible();
    await expect(page.getByLabel(/사용자명/i)).toBeVisible();
    await expect(page.getByLabel(/비밀번호/i)).toBeVisible();
  });

  test('should load register page', async ({ page }) => {
    await page.goto('/register');
    await expect(page.getByRole('heading', { name: /계정 만들기/i })).toBeVisible();
    await expect(page.getByLabel(/이메일/i)).toBeVisible();
  });

  test('API health check should pass', async ({ request }) => {
    const response = await request.get('/api/v1/health');
    expect(response.ok()).toBeTruthy();
    
    const data = await response.json();
    expect(data.status).toBe('healthy');
    expect(data.database).toBe('connected');
    expect(data.redis).toBe('connected');
  });

  test('WebSocket connection should work', async ({ page }) => {
    await page.goto('/');
    
    // Check if WebSocket connects
    const wsConnected = await page.evaluate(() => {
      return new Promise((resolve) => {
        const ws = new WebSocket('ws://localhost:8000/ws');
        ws.onopen = () => resolve(true);
        ws.onerror = () => resolve(false);
        setTimeout(() => resolve(false), 5000);
      });
    });
    
    expect(wsConnected).toBeTruthy();
  });

  test('should handle 404 pages', async ({ page }) => {
    await page.goto('/non-existent-page');
    await expect(page.getByText(/페이지를 찾을 수 없습니다|404/i)).toBeVisible();
  });

  test('should have proper CSP headers', async ({ page }) => {
    const response = await page.goto('/');
    const headers = response?.headers();
    
    expect(headers?.['x-content-type-options']).toBe('nosniff');
    expect(headers?.['x-frame-options']).toBe('SAMEORIGIN');
  });

  test('critical user flow should work', async ({ page }) => {
    // Go to login
    await page.goto('/login');
    
    // Click register link
    await page.getByText(/회원가입/i).click();
    await expect(page).toHaveURL(/register/);
    
    // Go back to login
    await page.getByText(/로그인/i).click();
    await expect(page).toHaveURL(/login/);
  });
});