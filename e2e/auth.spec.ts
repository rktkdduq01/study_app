import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should display login page', async ({ page }) => {
    // Check login page elements
    await expect(page.getByRole('heading', { name: /로그인/i })).toBeVisible();
    await expect(page.getByLabel(/사용자명 또는 이메일/i)).toBeVisible();
    await expect(page.getByLabel(/비밀번호/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /로그인/i })).toBeVisible();
    await expect(page.getByText(/계정이 없으신가요\?/i)).toBeVisible();
  });

  test('should show validation errors for empty fields', async ({ page }) => {
    // Click login without filling fields
    await page.getByRole('button', { name: /로그인/i }).click();

    // Check validation messages
    await expect(page.getByText(/사용자명 또는 이메일을 입력해주세요/i)).toBeVisible();
    await expect(page.getByText(/비밀번호를 입력해주세요/i)).toBeVisible();
  });

  test('should login successfully', async ({ page }) => {
    // Fill login form
    await page.getByLabel(/사용자명 또는 이메일/i).fill('testuser');
    await page.getByLabel(/비밀번호/i).fill('Test123!');
    
    // Submit form
    await page.getByRole('button', { name: /로그인/i }).click();

    // Wait for redirect to dashboard
    await page.waitForURL('**/dashboard');
    await expect(page.getByRole('heading', { name: /대시보드/i })).toBeVisible();
  });

  test('should show error for invalid credentials', async ({ page }) => {
    // Fill with invalid credentials
    await page.getByLabel(/사용자명 또는 이메일/i).fill('wronguser');
    await page.getByLabel(/비밀번호/i).fill('wrongpassword');
    
    // Submit form
    await page.getByRole('button', { name: /로그인/i }).click();

    // Check error message
    await expect(page.getByText(/잘못된 사용자명 또는 비밀번호입니다/i)).toBeVisible();
  });

  test('should navigate to register page', async ({ page }) => {
    // Click register link
    await page.getByText(/회원가입/i).click();

    // Check register page
    await page.waitForURL('**/register');
    await expect(page.getByRole('heading', { name: /계정 만들기/i })).toBeVisible();
  });

  test('should register new account', async ({ page }) => {
    // Navigate to register
    await page.goto('/register');

    // Fill registration form
    await page.getByLabel(/사용자명/i).fill('newuser');
    await page.getByLabel(/이메일/i).fill('newuser@example.com');
    await page.getByLabel(/비밀번호/i).first().fill('NewUser123!');
    await page.getByLabel(/비밀번호 확인/i).fill('NewUser123!');
    await page.getByLabel(/전체 이름/i).fill('New User');

    // Submit form
    await page.getByRole('button', { name: /가입하기/i }).click();

    // Should redirect to dashboard after successful registration
    await page.waitForURL('**/dashboard');
    await expect(page.getByText(/New User/i)).toBeVisible();
  });

  test('should logout successfully', async ({ page }) => {
    // Login first
    await page.getByLabel(/사용자명 또는 이메일/i).fill('testuser');
    await page.getByLabel(/비밀번호/i).fill('Test123!');
    await page.getByRole('button', { name: /로그인/i }).click();
    
    await page.waitForURL('**/dashboard');

    // Open user menu and logout
    await page.getByTestId('user-menu').click();
    await page.getByText(/로그아웃/i).click();

    // Should redirect to login
    await page.waitForURL('**/login');
    await expect(page.getByRole('heading', { name: /로그인/i })).toBeVisible();
  });

  test('should toggle password visibility', async ({ page }) => {
    const passwordInput = page.getByLabel(/비밀번호/i);
    const toggleButton = page.getByLabel(/비밀번호 표시/i);

    // Check initial state
    await expect(passwordInput).toHaveAttribute('type', 'password');

    // Toggle visibility
    await toggleButton.click();
    await expect(passwordInput).toHaveAttribute('type', 'text');

    // Toggle back
    await toggleButton.click();
    await expect(passwordInput).toHaveAttribute('type', 'password');
  });

  test('should persist login on page reload', async ({ page, context }) => {
    // Login
    await page.getByLabel(/사용자명 또는 이메일/i).fill('testuser');
    await page.getByLabel(/비밀번호/i).fill('Test123!');
    await page.getByRole('button', { name: /로그인/i }).click();
    
    await page.waitForURL('**/dashboard');

    // Reload page
    await page.reload();

    // Should still be on dashboard
    await expect(page).toHaveURL(/.*dashboard/);
    await expect(page.getByRole('heading', { name: /대시보드/i })).toBeVisible();
  });

  test('should handle session timeout', async ({ page }) => {
    // This test would require backend setup to simulate token expiration
    // For now, we'll test the UI behavior
    
    // Login
    await page.getByLabel(/사용자명 또는 이메일/i).fill('testuser');
    await page.getByLabel(/비밀번호/i).fill('Test123!');
    await page.getByRole('button', { name: /로그인/i }).click();
    
    await page.waitForURL('**/dashboard');

    // Simulate expired token by clearing localStorage
    await page.evaluate(() => {
      localStorage.removeItem('access_token');
    });

    // Try to navigate to protected route
    await page.goto('/quests');

    // Should redirect to login
    await page.waitForURL('**/login');
    await expect(page.getByRole('heading', { name: /로그인/i })).toBeVisible();
  });
});